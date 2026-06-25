"""
release_skill - 把已 publish 的 skill 推到外部 skill 仓(github release)

跟 publish-skill 的区别:
- publish-skill: 工具仓内部状态机(draft → published + 写 registry)
- release-skill: 对外发布,推到 lrrrq/proposal-skill 仓,自动 tag + 同步 registry

默认 dry-run,需 --apply 才真推。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from .config import Config
from .git_pusher import GitPusher, GitPusherError, make_temp_work_dir
from .registry import get_registry
from .utils import now_iso


def validate_version(version: str) -> Optional[str]:
    """
    校验 version 格式(vX.Y.Z),返回错误信息(有错时)或 None
    """
    import re
    if not re.match(r"^v\d+\.\d+\.\d+$", version):
        return f"version 格式不对: {version} (期望 vX.Y.Z,例如 v0.3.2)"
    return None


def release_skill(
    skill_id: str,
    repo: str = "lrrrq/proposal-skill",
    version: str = "",
    source: Optional[Path] = None,
    apply: bool = False,
    verbose: bool = False,
) -> Dict:
    """
    发布 skill 到外部 skill 仓

    Args:
        skill_id: Skill ID
        repo: 目标仓库 (lrrrq/proposal-skill 或 https://...)
        version: 版本号 (vX.Y.Z),必填
        source: 源目录 (默认 Config.PUBLISHED_DIR/skill_id)
        apply: 是否真推(默认 dry-run)
        verbose: 详细输出

    Returns:
        {
            "success": bool,
            "message": str,
            "plan": list,         # dry-run 时的执行计划
            "work_dir": str,      # 临时 work dir(已 cleanup)
            "pushed": bool,
            "version": str,
            "repo": str,
        }
    """
    plan = []

    # 1. 校验参数
    if not skill_id:
        return {"success": False, "message": "skill_id 必填", "plan": plan}

    err = validate_version(version)
    if err:
        return {"success": False, "message": err, "plan": plan}

    # 2. 校验 source
    if source is None:
        source = Config.PUBLISHED_DIR / skill_id
    source = Path(source)

    if not source.exists():
        return {
            "success": False,
            "message": f"source 目录不存在: {source}\n"
                       f"提示: 用 --source <dir> 指定,或先跑 publish-skill 准备好 published/{skill_id}/",
            "plan": plan,
        }

    # 3. 准备 registry 增量条目(从工具仓的 registry 读)
    registry = get_registry()
    skill_entry = registry.get_skill(skill_id)

    if not skill_entry:
        # 不在工具仓 registry 里也没关系,可以现场构造
        skill_entry = {
            "skill_id": skill_id,
            "display_name": skill_id,
            "status": "published",
            "quality_level": "unknown",
            "callable": True,
            "source_version": version,
            "published_at": now_iso(),
        }

    # 覆盖 version 字段(以命令行 --version 为准)
    skill_entry["source_version"] = version
    skill_entry["published_at"] = now_iso()

    registry_payload = {
        "skills": [skill_entry],
        "source_tool_repo": "lrrrq/proposal-skill-builder",
        "source_version": version,
    }

    # 4. 准备 commit message
    commit_message = f"release({skill_id}): {version}"

    # 5. 累积 plan
    plan.append(f"📂 source: {source}")
    plan.append(f"🎯 target: {repo}")
    plan.append(f"🏷  tag: {version}")
    plan.append(f"📝 commit: {commit_message}")
    plan.append(f"📋 registry entry: {skill_id} @ {version}")
    plan.append("")
    plan.append("Files to be synced:")
    for item in sorted(source.iterdir()):
        size = sum(p.stat().st_size for p in item.rglob("*") if p.is_file()) if item.is_dir() else item.stat().st_size
        kind = "dir" if item.is_dir() else "file"
        plan.append(f"  - [{kind}] {item.name} ({size:,} bytes)")
    plan.append("")
    plan.append(f"🛡  mode: {'APPLY (真推)' if apply else 'DRY-RUN (只报告)'}")

    if not apply:
        return {
            "success": True,
            "message": "dry-run 完成,未做任何修改。加 --apply 真推。",
            "plan": plan,
            "work_dir": None,
            "pushed": False,
            "version": version,
            "repo": repo,
        }

    # ===== 下面是 apply 模式 =====

    work_dir = make_temp_work_dir()
    pusher = GitPusher(repo=repo, work_dir=work_dir, verbose=verbose)

    try:
        # 6. 确认 gh auth
        pusher.ensure_gh_auth()

        # 7. 检查 target tag 不存在
        if pusher.tag_exists_remote(version):
            return {
                "success": False,
                "message": f"target 已有 tag {version},不覆盖。请 bump version 后重试。",
                "plan": plan,
                "work_dir": str(work_dir),
                "pushed": False,
                "version": version,
                "repo": repo,
            }

        # 8. clone target
        pusher.clone_target()

        # 9. sync source → target
        pusher.sync_source_to_target(source=source)

        # 10. 追加 registry
        pusher.append_registry(registry_payload)

        # 11. commit + tag
        pusher.commit_and_tag(version=version, message=commit_message)

        # 12. push
        pusher.push()

        return {
            "success": True,
            "message": f"✅ release 成功: {skill_id} {version} → {repo}",
            "plan": plan,
            "work_dir": str(work_dir),
            "pushed": True,
            "version": version,
            "repo": repo,
        }

    except GitPusherError as e:
        return {
            "success": False,
            "message": f"❌ release 失败: {e}",
            "plan": plan,
            "work_dir": str(work_dir),
            "pushed": False,
            "version": version,
            "repo": repo,
        }
    finally:
        pusher.cleanup()
