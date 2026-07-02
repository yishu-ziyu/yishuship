from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

PHASE_REQUIREMENTS = {
    "use-yishuship": [
        "vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md",
    ],
    "matt": [
        "vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/to-prd/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/to-issues/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/implement/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md",
        "vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md",
    ],
    "pm-intake": [
        "vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md",
        "vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/to-prd/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md",
    ],
    "design": [
        "vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/prototype/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/to-issues/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md",
    ],
    "dev": [
        "vendor/mattpocock-skills/skills/engineering/implement/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/diagnosing-bugs/SKILL.md",
    ],
    "e2e": [
        "vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md",
    ],
    "review": [
        "vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md",
    ],
    "refactor": [
        "vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md",
    ],
    "arch-design": [
        "vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md",
    ],
    "handoff": [
        "vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md",
        "vendor/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md",
    ],
    "qa": [
        "vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md",
    ],
    "write-docs": [
        "vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md",
        "vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md",
    ],
}


def skill_text(name: str) -> str:
    return (REPO_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class MattRuntimeActivationTests(unittest.TestCase):
    def test_required_upstream_files_exist(self) -> None:
        required = {path for paths in PHASE_REQUIREMENTS.values() for path in paths}
        for path in sorted(required):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

    def test_phase_skills_reference_required_upstream_paths(self) -> None:
        for phase, paths in PHASE_REQUIREMENTS.items():
            text = skill_text(phase)
            for path in paths:
                relative = "../../" + path
                self.assertIn(relative, text, f"{phase} must reference {relative}")

    def test_shared_standard_declares_runtime_activation(self) -> None:
        text = (REPO_ROOT / "skills/.shared/matt-pocock-standard.md").read_text(encoding="utf-8")
        self.assertIn("Runtime Activation", text)
        self.assertIn("using Matt", text)


if __name__ == "__main__":
    unittest.main()
