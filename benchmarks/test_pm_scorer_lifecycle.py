from __future__ import annotations

import unittest

from pm_scorer import (
    CHECKPOINTS,
    CHECKPOINT_DEFINITIONS,
    QUALITY_DIMENSIONS,
    score_full_pipeline,
    score_lifecycle_artifact,
    score_lifecycle_pipeline,
    score_stage,
)
from matt_flow_scorer import FLOW_DEFINITIONS, score_matt_flow


def rich_artifact(checkpoint: str) -> str:
    label = CHECKPOINT_DEFINITIONS[checkpoint]["label"]
    return f"""
# {label}

## Context
This section covers {label} for a real yishuship product task.
Evidence: https://example.com/research/{checkpoint}
User feedback sample: N=12, 7 repeated the same problem.
Competitor comparison: Existing tool A solves part of the workflow but misses the core scenario.

## Decision
Owner: PM
Action: convert this checkpoint into the next product or engineering artifact.
Acceptance criteria:
- Given the artifact exists, When engineering reads it, Then they can identify scope, constraints, and next steps.
- Risk: unclear ownership. Mitigation: assign one owner and one review gate.
"""


class LifecycleScorerTests(unittest.TestCase):
    def test_lifecycle_contract_stays_189_points(self) -> None:
        self.assertEqual(len(CHECKPOINTS), 21)
        self.assertEqual(QUALITY_DIMENSIONS, ("presence", "evidence", "actionability"))

        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS}
        result = score_lifecycle_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertTrue(result["all_pass"])
        self.assertEqual(set(result["checkpoints"].keys()), set(CHECKPOINTS))

    def test_each_checkpoint_scores_three_quality_dimensions(self) -> None:
        result = score_lifecycle_artifact("prd", rich_artifact("prd"))

        self.assertEqual(result["max"], 9)
        self.assertEqual(result["pass_threshold"], 6)
        self.assertTrue(result["passOrFail"])
        self.assertEqual(set(result["details"].keys()), {"presence", "evidence", "actionability"})

    def test_missing_checkpoint_fails_without_reducing_total_max(self) -> None:
        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS if checkpoint != "permission"}
        result = score_lifecycle_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertFalse(result["all_pass"])
        self.assertEqual(result["checkpoints"]["permission"]["total"], 0)
        self.assertFalse(result["checkpoints"]["permission"]["passOrFail"])

    def test_legacy_stage_api_still_works(self) -> None:
        stage_result = score_stage("discover", rich_artifact("scenario_research"))
        self.assertGreater(stage_result["max"], 0)
        self.assertIn("details", stage_result)

        pipeline_result = score_full_pipeline({"discover": rich_artifact("scenario_research")})
        self.assertGreater(pipeline_result["max"], 0)
        self.assertIn("stages", pipeline_result)

    def test_full_pipeline_accepts_lifecycle_outputs(self) -> None:
        outputs = {checkpoint: rich_artifact(checkpoint) for checkpoint in CHECKPOINTS}
        result = score_full_pipeline(outputs)

        self.assertEqual(result["max"], 189)
        self.assertIn("checkpoints", result)
        self.assertTrue(result["all_pass"])

    def test_matt_flow_full_chain_scores_as_hard_pass(self) -> None:
        item = {
            "expected_flow": {
                "required": [
                    "alignment",
                    "shared_language",
                    "prd_test_seams",
                    "vertical_slices",
                    "tdd",
                    "two_axis_review",
                    "handoff",
                ]
            }
        }
        output = """
## Route
/yishuship:pm-intake -> design -> dev -> review -> handoff

## Required flow steps
- alignment: run grill-with-docs first and update shared language in CONTEXT.md.
- prd_test_seams: create a PRD with Given/When/Then acceptance and test seams.
- vertical_slices: split into vertical slices / tracer bullets that can be independently verified.
- tdd: implement each slice with TDD red-green-refactor and a failing test first.
- two_axis_review: run Standards + Spec two-axis review against the PRD.
- handoff: write handoff artifacts for PR and CI release.
"""
        result = score_matt_flow(output, item)

        self.assertIn("two_axis_review", FLOW_DEFINITIONS)
        self.assertTrue(result["passOrFail"])
        self.assertEqual(result["total"], result["max"])

    def test_matt_flow_missing_required_step_fails(self) -> None:
        item = {
            "expected_flow": {
                "required": ["alignment", "prd_test_seams", "vertical_slices", "tdd"]
            }
        }
        output = """
先做 alignment，对齐用户问题。然后写 PRD 和验收标准，
再拆 vertical slices。最后直接实现。
"""
        result = score_matt_flow(output, item)

        self.assertFalse(result["passOrFail"])
        self.assertLess(result["total"], result["max"])
        self.assertFalse(result["details"]["required"]["tdd"]["hit"])

    def test_matt_flow_on_ramp_scores_prototype_and_diagnosis(self) -> None:
        prototype_item = {"expected_flow": {"required": ["alignment", "prototype"]}}
        prototype_output = "先 alignment 澄清问题，再做 throwaway prototype 给出 runnable answer。"
        self.assertTrue(score_matt_flow(prototype_output, prototype_item)["passOrFail"])

        diagnosis_item = {"expected_flow": {"required": ["diagnosis", "tdd"]}}
        diagnosis_output = "走 diagnosing-bugs：复现、最小化、提出 hypothesis、插桩，再用 TDD 回归测试修复。"
        self.assertTrue(score_matt_flow(diagnosis_output, diagnosis_item)["passOrFail"])


if __name__ == "__main__":
    unittest.main()
