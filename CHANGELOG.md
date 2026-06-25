# Changelog

All notable changes to proposal-skill-builder are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `inspect-source-drift` CLI command: list source_files rows whose
  `current_path` no longer exists on disk (read-only).
- `repair-source-drift [--apply]` CLI command: mark drift rows in
  `source_files.error_message`. Defaults to dry-run; requires
  `--apply` to actually write.
- `skill_builder/drift_check.py` module backing both commands.
- `tests/test_cross_platform.py` — 10 unit tests covering path config,
  DB init, drift detection, drift repair, and LibreOffice lookup on
  any platform.
- `.github/workflows/test.yml` — CI matrix over `ubuntu-latest`,
  `macos-latest`, `windows-latest` × Python 3.9-3.12.
- **`release-skill <skill_id>` CLI command**: push a published skill to an
  external skill repository (e.g. `lrrrq/proposal-skill`), with automatic
  `git tag` and `skill_registry.json` sync. Defaults to dry-run; pass
  `--apply` to actually push. Required args: `--version vX.Y.Z`. Optional
  args: `--repo` (default `lrrrq/proposal-skill`), `--source` (default
  `Config.PUBLISHED_DIR/<skill_id>`), `--verbose`.
- `skill_builder/git_pusher.py` — thin wrapper around `gh` CLI that
  clones the target repo into a temp work dir, syncs source files
  (preserving `.git`, `README.md`, `.gitignore`, `docs/`), merges
  `registry/skill_registry.json`, commits, tags, and pushes. Cleans
  up the work dir on exit. Sets `http.postBuffer 524288000` to handle
  the brand-style-pack reference images (the ~2 MB push case that
  bit us during the v0.3.1 release).
- `skill_builder/release_skill.py` — orchestrates the release flow,
  validates the `vX.Y.Z` version, refuses to overwrite an existing
  remote tag, and surfaces `GitPusherError` as a friendly failure
  message.

### Fixed
- `office_converter.find_libreoffice_executable`: added Windows candidates
  (`C:\Program Files\LibreOffice\program\soffice.exe` and 32-bit variant)
  and made the function portable. Now relies on `shutil.which` first and
  only falls back to platform-specific absolute paths.
- `office_converter.convert_pptx_to_pdf`: force `encoding="utf-8"` on
  `subprocess.run(text=True)` to avoid GBK default encoding on Chinese
  Windows machines.

### Documentation
- README rewritten to cover the full CLI, cross-platform support,
  drift detection, project structure, and roadmap.
- LICENSE (MIT) added.

## [0.2.0] - 2026-06-12

### Added
- proposal-reference-transfer v0.2 skill (M Films brand pack, evals,
  page header/footer DNA, anti-patterns).
- Visual language extended to 6 dimensions.

## [0.1.0] - 2026-06-08

### Added
- Initial CLI scaffold (`init`, `status`, `intake`, `create-case`,
  `compile-case`, `extract-patterns`, etc.).
- SQLite schema: `source_files`, `cases`, `jobs`, `skills`.
- Path layout: `source_proposals/{staging,accepted,duplicates,rejected}`,
  `compiled/cases/`, `skills/{draft,published,quarantine}/`,
  `registry/`, `reports/`.