"""yishuship PM benchmark data loader.

加载 PM 场景数据集：每个 item 是一个产品场景 + 目标阶段 + ground truth 评分。
"""
from __future__ import annotations

import json
from pathlib import Path

from skillopt.datasets.base import SplitDataLoader


def _normalize_item(raw: dict) -> dict:
    item = {
        "id": str(raw.get("id") or raw.get("uid") or ""),
        "scenario": str(raw.get("scenario") or ""),
        "stage": str(raw.get("stage") or "discover"),
        "context": str(raw.get("context") or ""),
        "ground_truth_keywords": raw.get("ground_truth_keywords") or [],
        "task_type": str(raw.get("stage") or "discover"),
    }
    if "expected_flow" in raw:
        item["expected_flow"] = raw["expected_flow"]
        item["task_type"] = "matt-flow"
    return item


class YishushipLoader(SplitDataLoader):

    def load_split_items(self, split_path: str) -> list[dict]:
        path = Path(split_path)
        json_files = sorted(path.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No .json found in {split_path}")
        with json_files[0].open(encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError(f"Expected JSON array in {json_files[0]}")
        return [_normalize_item(item) for item in raw]
