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