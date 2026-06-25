"""
git_pusher - 封装 gh CLI 操作,把 skill 资产推到外部 skill 仓

设计要点:
- 默认 dry-run,所有写操作需要 --apply
- 用 gh CLI(已在 PATH + 已 auth),不走 git 协议直接拼
- 失败时清理 work_dir(本地 clone),不污染系统
- 所有错误用 raise 抛出,调用方负责 try/except
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")


class GitPusherError(Exception):
    """git_pusher 通用错误"""
    pass


class GitPusher:
    """
    封装 git/gh CLI 操作,把 skill 推到外部 skill 仓

    使用模式:
        pusher = GitPusher(repo="lrrrq/proposal-skill", work_dir=...)
        pusher.clone_target()
        pusher.sync_source_to_target(source=Path("..."))
        pusher.append_registry(registry=...)
        pusher.commit_and_tag(version="v0.3.2", message="...")
        pusher.push()  # 真推
        pusher.cleanup()  # 清理 work_dir
    """

    def __init__(self, repo: str, work_dir: Path, verbose: bool = False):
        """
        Args:
            repo: 目标仓库,可以是 "lrrrq/proposal-skill" 或 "https://github.com/..."
            work_dir: 本地 clone 目录(临时)
            verbose: 详细输出
        """
        if not repo:
            raise GitPusherError("repo 不能为空")

        self.repo = repo
        self.work_dir = Path(work_dir)
        self.verbose = verbose
        self._cloned = False

    # ---------- helpers ----------

    def _normalize_repo(self) -> str:
        """
        规范化 repo 名称为 "owner/repo" 形式,用于 gh CLI
        """
        r = self.repo.strip()
        if r.startswith("https://github.com/"):
            r = r[len("https://github.com/"):]
        elif r.startswith("git@github.com:"):
            r = r[len("git@github.com:"):]
        if r.endswith(".git"):
            r = r[:-4]
        return r.rstrip("/")

    def _run(self, cmd: list, cwd: Optional[Path] = None, check: bool = True,
             capture: bool = False) -> subprocess.CompletedProcess:
        """
        跑 subprocess,统一处理
        """
        kwargs = {
            "shell": False,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if cwd is not None:
            kwargs["cwd"] = str(cwd)
        if capture:
            kwargs["capture_output"] = True
        else:
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.PIPE

        if self.verbose:
            print(f"  $ {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, **kwargs)
        except FileNotFoundError as e:
            raise GitPusherError(f"命令未找到: {cmd[0]} ({e})")

        if check and result.returncode != 0:
            stderr = result.stderr if capture else ""
            raise GitPusherError(
                f"命令失败 (rc={result.returncode}): {' '.join(cmd)}\nstderr: {stderr}"
            )

        return result

    # ---------- main operations ----------

    def ensure_gh_auth(self) -> None:
        """
        确认 gh CLI 已 auth(必须含 repo scope)
        """
        result = self._run(["gh", "auth", "status"], capture=True, check=False)
        if result.returncode != 0:
            raise GitPusherError(
                "gh CLI 未 auth,跑 `gh auth login` 修一下\n"
                f"stderr: {result.stderr}"
            )

    def tag_exists_remote(self, version: str) -> bool:
        """
        检查目标仓是否已有该 tag
        """
        if not VERSION_RE.match(version):
            raise GitPusherError(f"version 格式不对: {version} (期望 vX.Y.Z)")

        repo = self._normalize_repo()
        result = self._run(
            ["gh", "api", f"repos/{repo}/git/refs/tags/{version}"],
            capture=True, check=False,
        )
        return result.returncode == 0

    def clone_target(self) -> None:
        """
        用 gh repo clone 拉取目标仓到 work_dir
        """
        if self.work_dir.exists():
            raise GitPusherError(f"work_dir 已存在: {self.work_dir}")

        repo = self._normalize_repo()
        self.work_dir.parent.mkdir(parents=True, exist_ok=True)

        self._run(["gh", "repo", "clone", repo, str(self.work_dir)])
        self._cloned = True

    def sync_source_to_target(
        self,
        source: Path,
        preserve_dirs: Optional[list] = None,
    ) -> None:
        """
        把 source 目录里的内容(非 .git 目录)同步到 target

        Args:
            source: 源目录
            preserve_dirs: 要保留(不删不覆盖)的目录列表,默认 [".git", "README.md", ".gitignore", "docs"]
        """
        if not self._cloned:
            raise GitPusherError("先 clone_target()")

        if not source.exists():
            raise GitPusherError(f"source 不存在: {source}")

        if preserve_dirs is None:
            preserve_dirs = [".git", "README.md", ".gitignore", "docs"]

        # 1. 删除 target 里要覆盖的旧内容(保留 preserve_dirs)
        for item in self.work_dir.iterdir():
            if item.name in preserve_dirs:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # 2. 复制 source 全部内容到 target
        for item in source.iterdir():
            dst = self.work_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)

    def append_registry(self, registry_data: dict, registry_filename: str = "skill_registry.json") -> None:
        """
        追加/合并 registry 到 target

        策略:
        - target 已有 registry → 合并(skill_id 已存在则更新,不存在则追加)
        - target 无 registry → 直接写
        """
        if not self._cloned:
            raise GitPusherError("先 clone_target()")

        registry_path = self.work_dir / registry_filename

        existing = {"skills": [], "updated_at": None}
        if registry_path.exists():
            import json
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # 坏的 registry 当成空

        existing_skills = {s.get("skill_id"): s for s in existing.get("skills", [])}
        new_skills = registry_data.get("skills", [])
        for s in new_skills:
            sid = s.get("skill_id")
            if sid:
                existing_skills[sid] = s

        from datetime import datetime
        merged = {
            "skills": list(existing_skills.values()),
            "updated_at": datetime.now().isoformat(),
        }

        import json
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

    def commit_and_tag(self, version: str, message: str) -> None:
        """
        git add all + commit + tag

        注意: 不 push,只本地提交 + tag
        """
        if not self._cloned:
            raise GitPusherError("先 clone_target()")

        if not VERSION_RE.match(version):
            raise GitPusherError(f"version 格式不对: {version}")

        # 配置 git user(避免 commit 失败)
        self._run(["git", "config", "user.email", "skill-builder@local"], cwd=self.work_dir, check=False)
        self._run(["git", "config", "user.name", "skill-builder"], cwd=self.work_dir, check=False)

        # 调大 postBuffer(防大文件 push 失败,跟 memory 坑 2 一样)
        self._run(
            ["git", "config", "http.postBuffer", "524288000"],
            cwd=self.work_dir, check=False,
        )

        # add all
        self._run(["git", "add", "-A"], cwd=self.work_dir)

        # commit(可能没改动,允许失败)
        result = self._run(
            ["git", "commit", "-m", message, "--allow-empty"],
            cwd=self.work_dir, check=False, capture=True,
        )
        # 实际上 --allow-empty 不会失败,所以 commit 应该一定成功
        if result.returncode != 0:
            raise GitPusherError(f"commit 失败: {result.stderr}")

        # tag
        result = self._run(
            ["git", "tag", "-a", version, "-m", message],
            cwd=self.work_dir, check=False, capture=True,
        )
        if result.returncode != 0:
            raise GitPusherError(f"tag 创建失败: {result.stderr}")

    def push(self) -> None:
        """
        git push origin main + push tag
        """
        if not self._cloned:
            raise GitPusherError("先 clone_target()")

        # push main
        result = self._run(
            ["git", "push", "origin", "main"],
            cwd=self.work_dir, check=False, capture=True,
        )
        if result.returncode != 0:
            raise GitPusherError(f"push main 失败: {result.stderr}")

        # push tag
        result = self._run(
            ["git", "push", "origin", "--tags"],
            cwd=self.work_dir, check=False, capture=True,
        )
        if result.returncode != 0:
            raise GitPusherError(f"push tag 失败: {result.stderr}")

    def cleanup(self) -> None:
        """
        删 work_dir(无论成功失败都该调)
        """
        if self.work_dir.exists() and self._cloned:
            try:
                shutil.rmtree(self.work_dir)
            except OSError:
                pass  # cleanup 失败不阻塞
            self._cloned = False


def make_temp_work_dir(prefix: str = "skill_release_") -> Path:
    """
    创建一个临时 work_dir,平台无关
    """
    return Path(tempfile.mkdtemp(prefix=prefix))
