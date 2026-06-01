import json
import tempfile
import unittest
from pathlib import Path

from skill_builder.router_v2 import (
    RouterV2,
    decompose_brief,
    resolve_constraints,
)


FIXTURES_DIR = Path("tests/fixtures")
ROUTER_REGISTRY = FIXTURES_DIR / "router_v2_registry.json"
SOURCE_PATTERNS = FIXTURES_DIR / "router_v2_source_patterns.json"


class RouterV2Test(unittest.TestCase):
    def router(self):
        return RouterV2(registry_path=ROUTER_REGISTRY, source_patterns_path=SOURCE_PATTERNS)

    def test_decompose_brief_keeps_explicit_business_goal(self):
        brief = Path("tests/fixtures/w_hotel_tvc_brief.txt").read_text(encoding="utf-8")

        analysis = decompose_brief(brief)

        self.assertEqual(analysis["business_goal"], "推广端午礼盒预订")
        self.assertNotIn("business_goal", analysis["missing_information"])
        self.assertEqual(analysis["brand_or_subject"], "W酒店")
        self.assertEqual(analysis["project_type"], "TVC")
        self.assertIn("土金色", analysis["explicit_forbidden"])

    def test_constraints_treat_bad_gold_as_current_brief_constraint_only(self):
        analysis = decompose_brief("广州W酒店TVC，业务目标是推广礼盒预订，不要土金色。")

        constraints = resolve_constraints(analysis, [])

        visual_rules = [item for item in constraints["constraints"] if item["type"] == "visual"]
        self.assertTrue(any(item["source"] == "brief" for item in visual_rules))
        self.assertTrue(any(item["rule"] == "避免土金色" for item in visual_rules))
        self.assertTrue(any("本次 brief" in item["reason"] for item in visual_rules))
        self.assertFalse(any(item["rule"] == "禁止使用金色" for item in visual_rules))

    def test_constraints_treat_plain_gold_ban_as_current_brief_only(self):
        analysis = decompose_brief("广州W酒店TVC，业务目标是推广礼盒预订，不要金色。")

        constraints = resolve_constraints(analysis, [])

        visual_rules = [item for item in constraints["constraints"] if item["type"] == "visual"]
        self.assertTrue(any(item["rule"] == "避免金色" for item in visual_rules))
        self.assertTrue(any("本次 brief" in item["reason"] for item in visual_rules))
        self.assertFalse(any(item["rule"] == "永久禁止金色" for item in visual_rules))

    def test_constraints_allow_confirmed_gold_accent(self):
        analysis = decompose_brief("广州W酒店TVC，业务目标是品牌心智建立，品牌要求金色点缀。")

        constraints = resolve_constraints(analysis, [])

        self.assertTrue(any(
            item["source"] == "brief"
            and item["strength"] == "soft"
            and "金色点缀" in item["rule"]
            for item in constraints["constraints"]
        ))

    def test_router_v2_uses_only_v2_registry_and_four_assets(self):
        brief = Path("tests/fixtures/w_hotel_tvc_brief.txt").read_text(encoding="utf-8")

        result = self.router().route(brief)

        self.assertTrue(result["supported"])
        self.assertEqual(result["skill_ids"], [
            "v2.w_hotel.brand",
            "v2.w_hotel.video_strategy",
            "v2.w_hotel.output_structure",
            "v2.w_hotel.language_style",
        ])
        self.assertEqual(len(result["context_packet"]["skills"]), 4)
        self.assertNotIn("luxury-hotel-festival", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("case_", json.dumps(result, ensure_ascii=False))
        self.assertIn("source_material", json.dumps(result["constraints"], ensure_ascii=False))

    def test_source_material_constraints_are_soft_candidate_evidence(self):
        brief = Path("tests/fixtures/w_hotel_tvc_brief.txt").read_text(encoding="utf-8")

        result = self.router().route(brief)

        source_constraints = [
            item for item in result["constraints"]["constraints"]
            if item["source"] == "source_material"
        ]
        self.assertTrue(source_constraints)
        self.assertTrue(all(item["strength"] == "soft" for item in source_constraints))
        self.assertTrue(all("source_doc_id" in item["reason"] for item in source_constraints))
        self.assertNotIn("case_", json.dumps(result, ensure_ascii=False))

    def test_router_v2_rejects_unsupported_brief_without_fallback(self):
        result = self.router().route("某汽车品牌发布会活动方案，需要完整执行规划。")

        self.assertFalse(result["supported"])
        self.assertIn("Phase 1", result["reason"])
        self.assertEqual(result["skill_ids"], [])

    def test_render_md_outputs_proposal_sections_without_ppt(self):
        brief = Path("tests/fixtures/w_hotel_tvc_brief.txt").read_text(encoding="utf-8")
        result = self.router().route(brief)

        md = result["proposal_md"]

        for section in [
            "## 1. Brief 摘要",
            "## 2. 关键判断",
            "## 3. 核心洞察",
            "## 4. 创意命题",
            "## 5. 影片结构",
            "## 6. 视觉与参考方向",
            "## 7. 传播价值",
            "## 8. 动态约束与禁忌",
            "## 9. 待确认问题",
        ]:
            self.assertIn(section, md)

        self.assertIn("证据", md)
        self.assertNotIn("生成PPT", md)
        self.assertNotIn("器材清单", md)

    def test_write_output_file(self):
        brief = Path("tests/fixtures/w_hotel_tvc_brief.txt").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "proposal.md"

            result = self.router().route_to_file(brief, output)

            self.assertTrue(result["supported"])
            self.assertTrue(output.exists())
            self.assertIn("# W酒店端午节TVC创意提案", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
