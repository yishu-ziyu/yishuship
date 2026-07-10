#!/usr/bin/env python3
"""Execution model wiring: shared doc exists and key skills reference it."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SHARED = REPO / "skills" / ".shared" / "execution-model.md"
MUST_REF = [
    REPO / "skills" / "use-yishuship" / "SKILL.md",
    REPO / "skills" / "auto" / "SKILL.md",
    REPO / "skills" / "design" / "SKILL.md",
    REPO / "skills" / "dev" / "SKILL.md",
]


class ExecutionModelTests(unittest.TestCase):
    def test_shared_file_exists_and_has_three_layers(self) -> None:
        self.assertTrue(SHARED.is_file(), str(SHARED))
        text = SHARED.read_text(encoding="utf-8")
        self.assertIn("Layer 1", text)
        self.assertIn("Layer 2", text)
        self.assertIn("Layer 3", text)
        self.assertIn("Intra-stage", text)
        self.assertIn("Failure", text)

    def test_key_skills_reference_execution_model(self) -> None:
        for path in MUST_REF:
            body = path.read_text(encoding="utf-8")
            self.assertIn(
                "execution-model.md",
                body,
                f"{path} must reference execution-model.md",
            )

    def test_dec_0007_exists(self) -> None:
        dec = REPO / "docs" / "decisions" / "DEC-0007-execution-model.md"
        self.assertTrue(dec.is_file())


if __name__ == "__main__":
    unittest.main()
