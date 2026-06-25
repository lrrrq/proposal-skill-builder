"""Cross-platform smoke test for proposal-skill-builder.

Run with:

    python3 -m pytest tests/test_cross_platform.py -v
or
    python3 tests/test_cross_platform.py

Why this exists
---------------
proposal-skill-builder ships a few CLI commands whose behaviour depends
on the host OS (path separators, encoding, LibreOffice lookup). This
test pins the cross-platform invariants so a CI matrix catches regressions
before users hit them. Tests use only the standard library + the bundled
modules; no external network, no AI calls.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from skill_builder.config import Config  # noqa: E402
from skill_builder.db import (  # noqa: E402
    get_connection, init_db, run_migrations, ALLOWED_TABLES,
)


class PathConfigTest(unittest.TestCase):
    """Config must derive paths from __file__, not absolute OS-specific roots."""

    def test_project_root_is_absolute(self) -> None:
        self.assertTrue(Config.PROJECT_ROOT.is_absolute())

    def test_paths_use_pathlib(self) -> None:
        for attr in ("STAGING_DIR", "ACCEPTED_DIR", "DATA_DIR", "DB_PATH",
                     "COMPILED_DIR", "REPORTS_DIR", "SKILLS_DIR", "REGISTRY_DIR"):
            value = getattr(Config, attr)
            self.assertIsInstance(value, Path, f"{attr} must be a Path")

    def test_db_path_under_data_dir(self) -> None:
        self.assertEqual(Config.DB_PATH.parent, Config.DATA_DIR)
        self.assertEqual(Config.DB_PATH.name, "skill_builder.db")

    def test_db_path_is_inside_project_root(self) -> None:
        # DB_PATH must be a descendant of PROJECT_ROOT — this is the only
        # invariant we actually need. (We previously tried to assert that
        # the path did not contain the user's home directory, but on
        # GitHub Actions runners the checkout lands at
        # $HOME/work/<repo>/<repo>/, so PROJECT_ROOT legitimately lives
        # under $HOME. That assertion was wrong and broke CI.)
        self.assertTrue(
            str(Config.DB_PATH).startswith(str(Config.PROJECT_ROOT) + str(Path("/")))
            or Config.DB_PATH.parent == Config.PROJECT_ROOT / "data"
        )


class DatabaseInitTest(unittest.TestCase):
    """init_db + run_migrations must succeed on every platform."""

    def setUp(self) -> None:
        # Use a sandbox DB so we never touch the real one during tests.
        self.tmpdir = Path(tempfile.mkdtemp(prefix="psb-db-"))
        self.db_path = self.tmpdir / "skill_builder.db"
        # Patch Config.DB_PATH for the duration of this test
        self._original_db_path = Config.DB_PATH
        Config.DB_PATH = self.db_path  # type: ignore[assignment]

    def tearDown(self) -> None:
        Config.DB_PATH = self._original_db_path  # type: ignore[assignment]
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_expected_tables(self) -> None:
        init_db()
        run_migrations()
        con = sqlite3.connect(str(self.db_path))
        try:
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {r[0] for r in cur.fetchall()}
        finally:
            con.close()
        # Core tables must all exist
        for required in ALLOWED_TABLES:
            self.assertIn(required, tables, f"missing table: {required}")

    def test_insert_and_query_unicode(self) -> None:
        """Chinese filenames and emoji must round-trip through the DB."""
        init_db()
        run_migrations()
        con = get_connection()
        try:
            con.execute(
                "INSERT INTO source_files (file_id, original_filename, current_path, "
                "sha256, status) VALUES (?, ?, ?, ?, ?)",
                ("abc123456789", "ALSO 「兴趣填空」情绪短片.pdf",
                 "/tmp/also.pdf", "deadbeef" * 8, "accepted"),
            )
            con.commit()
            row = con.execute(
                "SELECT original_filename FROM source_files WHERE file_id=?",
                ("abc123456789",),
            ).fetchone()
            self.assertEqual(row[0], "ALSO 「兴趣填空」情绪短片.pdf")
        finally:
            con.close()


class DriftCheckTest(unittest.TestCase):
    """inspect_source_drift + repair_source_drift work on any filesystem layout."""

    def setUp(self) -> None:
        # Sandbox: copy the real DB aside, point Config at a temp one.
        self.tmpdir = Path(tempfile.mkdtemp(prefix="psb-drift-"))
        self.db_path = self.tmpdir / "skill_builder.db"
        self.accepted_dir = self.tmpdir / "source_proposals" / "accepted"
        self.accepted_dir.mkdir(parents=True)
        self._original_db_path = Config.DB_PATH
        self._original_accepted_dir = Config.ACCEPTED_DIR
        Config.DB_PATH = self.db_path  # type: ignore[assignment]
        Config.ACCEPTED_DIR = self.accepted_dir  # type: ignore[assignment]
        init_db()
        run_migrations()

    def tearDown(self) -> None:
        Config.DB_PATH = self._original_db_path  # type: ignore[assignment]
        Config.ACCEPTED_DIR = self._original_accepted_dir  # type: ignore[assignment]
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _insert_source_file(self, file_id: str, name: str, path: Path) -> None:
        con = get_connection()
        try:
            con.execute(
                "INSERT INTO source_files (file_id, original_filename, current_path, "
                "sha256, status) VALUES (?, ?, ?, ?, ?)",
                (file_id, name, str(path), "a" * 64, "accepted"),
            )
            con.commit()
        finally:
            con.close()

    def test_inspect_reports_drift_only_for_missing(self) -> None:
        from skill_builder.drift_check import inspect_source_drift
        # One file on disk, one missing
        on_disk = self.accepted_dir / "real.md"
        on_disk.write_text("# real\n", encoding="utf-8")
        self._insert_source_file("real123456789", "real.md", on_disk)
        self._insert_source_file("ghost23456789", "ghost.md",
                                 self.accepted_dir / "ghost.md")

        result = inspect_source_drift(dataset="all")
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual(result["missing"][0]["file_id"], "ghost23456789")

    def test_repair_dry_run_does_not_touch_db(self) -> None:
        from skill_builder.drift_check import repair_source_drift
        self._insert_source_file("ghost23456789", "ghost.md",
                                 self.accepted_dir / "ghost.md")
        repair_source_drift(dataset="all", dry_run=True)
        con = get_connection()
        try:
            row = con.execute(
                "SELECT error_message FROM source_files WHERE file_id=?",
                ("ghost23456789",),
            ).fetchone()
            self.assertIsNone(row[0])
        finally:
            con.close()

    def test_repair_apply_sets_error_message(self) -> None:
        from skill_builder.drift_check import repair_source_drift
        self._insert_source_file("ghost23456789", "ghost.md",
                                 self.accepted_dir / "ghost.md")
        result = repair_source_drift(dataset="all", dry_run=False)
        self.assertEqual(result["marked"], 1)
        con = get_connection()
        try:
            row = con.execute(
                "SELECT error_message FROM source_files WHERE file_id=?",
                ("ghost23456789",),
            ).fetchone()
            self.assertIsNotNone(row[0])
            self.assertIn("source drift", row[0])
        finally:
            con.close()


class OfficeConverterTest(unittest.TestCase):
    """find_libreoffice_executable must not raise on any platform."""

    def test_lookup_does_not_crash(self) -> None:
        from skill_builder.office_converter import find_libreoffice_executable
        # Either it finds LibreOffice or it returns None. Either is fine,
        # but it must not raise — Windows would previously blow up on
        # the literal `/Applications/...` candidates.
        result = find_libreoffice_executable()
        if result is not None:
            self.assertTrue(result.exists(), f"returned path missing: {result}")


if __name__ == "__main__":
    unittest.main()