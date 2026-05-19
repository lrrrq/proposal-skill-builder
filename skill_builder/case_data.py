"""
Case data loading - centralized case artifact management
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Union

from .config import Config


@dataclass
class CaseData:
    """Container for all case artifacts"""
    case_id: str
    fragments: List[Dict]
    ai_fragments: List[Dict]
    patterns: List[Dict]
    strategies: List[Dict]
    assets: List[Dict]
    compressed: List[Dict]
    pages: List[Dict]
    descriptions: List[Dict]


class CaseDataLoader:
    """Centralized case artifact loading"""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.case_dir = Config.CASES_DIR / case_id

    def _load_json(self, filename: str) -> List[Dict]:
        """Internal helper to load JSON file"""
        path = self.case_dir / filename
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_fragments(self) -> List[Dict]:
        path = self.case_dir / "fragments.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_ai_fragments(self) -> List[Dict]:
        path = self.case_dir / "ai_fragments.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_patterns(self) -> List[Dict]:
        path = self.case_dir / "patterns.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_strategies(self) -> List[Dict]:
        path = self.case_dir / "strategies.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_assets(self) -> List[Dict]:
        path = self.case_dir / "assets.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_compressed(self) -> List[Dict]:
        path = self.case_dir / "compressed_fragments.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_pages(self) -> List[Dict]:
        path = self.case_dir / "pages.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_descriptions(self) -> List[Dict]:
        path = self.case_dir / "descriptions.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all(self) -> CaseData:
        """Load all artifacts"""
        return CaseData(
            case_id=self.case_id,
            fragments=self.load_fragments(),
            ai_fragments=self.load_ai_fragments(),
            patterns=self.load_patterns(),
            strategies=self.load_strategies(),
            assets=self.load_assets(),
            compressed=self.load_compressed(),
            pages=self.load_pages(),
            descriptions=self.load_descriptions(),
        )

    def save_json(self, filename: str, data: Union[list, dict]):
        """Helper to save JSON atomically"""
        path = self.case_dir / filename
        tmp = Path(str(path) + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)