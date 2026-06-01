import json
import tempfile
import unittest
from pathlib import Path

from skill_builder.config import Config
from skill_builder.source_knowledge_extractor import (
    SourceKnowledgeError,
    extract_source_knowledge,
    extract_source_knowledge_to_file,
    load_pdf_pages,
    select_signal_pages,
)


W_HOTEL_PDF = Config.ACCEPTED_DIR / "W酒店中秋创意概要M Films0705V1(2).pdf"


@unittest.skipUnless(W_HOTEL_PDF.exists(), "requires local source proposal fixture")
class SourceKnowledgeExtractorTest(unittest.TestCase):
    def test_load_pdf_pages_from_original_pdf(self):
        pages = load_pdf_pages(W_HOTEL_PDF)

        self.assertGreater(len(pages), 5)
        self.assertEqual(pages[0]["page_number"], 1)
        self.assertIsInstance(pages[0]["text"], str)

    def test_select_signal_pages_filters_cover_and_contents_noise(self):
        pages = load_pdf_pages(W_HOTEL_PDF)

        signal_pages = select_signal_pages(pages)
        page_numbers = [page["page_number"] for page in signal_pages]

        self.assertNotIn(1, page_numbers)
        self.assertTrue(all(1 <= page <= len(pages) for page in page_numbers))
        self.assertTrue(page_numbers)

    def test_extract_source_knowledge_uses_source_doc_fields_not_case_fields(self):
        result = extract_source_knowledge([W_HOTEL_PDF])

        self.assertEqual(result["schema_version"], "source_patterns.v2")
        self.assertEqual(len(result["source_files"]), 1)
        self.assertTrue(result["patterns"])

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("case_", serialized)
        self.assertNotIn("luxury-hotel-festival", serialized)

        for pattern in result["patterns"]:
            self.assertEqual(set(pattern), {
                "source_doc_id",
                "source_file",
                "page_refs",
                "judgement_logic",
                "proposal_flow",
                "brand_constraints",
                "pattern",
                "rules",
                "applicable_when",
                "not_applicable_when",
            })
            self.assertEqual(len(pattern["source_doc_id"]), 12)
            self.assertTrue(pattern["source_file"].startswith("source_proposals/accepted/"))
            self.assertTrue(pattern["page_refs"])
            self.assertTrue(all(isinstance(page, int) for page in pattern["page_refs"]))
            self.assertTrue(pattern["judgement_logic"])
            self.assertTrue(pattern["proposal_flow"])
            self.assertTrue(pattern["brand_constraints"]["prefer"])
            self.assertIn("hard", pattern["rules"])
            self.assertIn("soft", pattern["rules"])

    def test_rejects_non_pdf_and_old_artifact_paths(self):
        with self.assertRaises(SourceKnowledgeError):
            extract_source_knowledge([Config.CASES_DIR / "case_0001" / "case_card.md"])

        with self.assertRaises(SourceKnowledgeError):
            extract_source_knowledge([Config.PUBLISHED_DIR / "luxury-hotel-festival" / "SKILL.md"])

    def test_extract_source_knowledge_to_file_writes_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "source_patterns.json"

            result = extract_source_knowledge_to_file([W_HOTEL_PDF], output)

            self.assertTrue(output.exists())
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(written["patterns"], result["patterns"])


if __name__ == "__main__":
    unittest.main()
