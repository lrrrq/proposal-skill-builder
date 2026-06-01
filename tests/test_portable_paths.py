import tempfile
import unittest
from pathlib import Path

from skill_builder.compiler import compile_image_case
from skill_builder.config import Config


class PortablePathTest(unittest.TestCase):
    def test_project_paths_are_stored_relative_and_resolved_from_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_root = Config.PROJECT_ROOT
            Config.PROJECT_ROOT = Path(tmpdir)
            try:
                source = Config.PROJECT_ROOT / "source_proposals" / "accepted" / "sample.jpg"
                case_dir = Config.PROJECT_ROOT / "compiled" / "cases" / "case_test"
                source.parent.mkdir(parents=True)
                (case_dir / "visual_assets").mkdir(parents=True)
                source.write_bytes(b"not a real image")

                result = compile_image_case("case_test", source, case_dir)

                stored_path = result["assets"][0]["stored_path"]
                self.assertEqual(stored_path, "compiled/cases/case_test/visual_assets/sample.jpg")
                self.assertFalse(Path(stored_path).is_absolute())
                self.assertTrue(Config.resolve_path(stored_path).exists())
            finally:
                Config.PROJECT_ROOT = original_root


if __name__ == "__main__":
    unittest.main()
