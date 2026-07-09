#!/usr/bin/env python3
"""
End-to-end tests for yishuship's long-horizon stability mechanisms.

Tests three critical assumptions:
  1. pm-gate.sh blocks Agent subagent calls when PM artifacts are missing
  2. pm-verify.sh signals phase completion
  3. An agent cannot bypass gates by modifying markers (structural defense)
  4. auto-orchestrate.sh state machine works end-to-end
  5. phase-guardrail.sh enforces per-phase artifact isolation
  6. stop-gate.sh blocks exit when task is incomplete
  7. Artifact format resilience (JSON vs MD corruption)
  8. Cross-session resume: init → partial progress → resume carries context

IMPORTANT: Claude Code hooks return rc=0 even when blocking. The block
decision is communicated via stdout JSON: {"decision":"block","reason":"..."}.
Tests must check stdout for the block decision, not the return code.

Run: python3 benchmarks/test_long_horizon_e2e.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


# ── paths ─────────────────────────────────────────────────────

REPO_ROOT = "/Users/mahaoxuan/Developer/yishuship"
GATE_SCRIPT = f"{REPO_ROOT}/scripts/pm-gate.sh"
VERIFY_SCRIPT = f"{REPO_ROOT}/scripts/pm-verify.sh"
GUARDRAIL_SCRIPT = f"{REPO_ROOT}/scripts/phase-guardrail.sh"
ORCH_SCRIPT = f"{REPO_ROOT}/scripts/auto-orchestrate.sh"


# ── helpers ──────────────────────────────────────────────────

def run_hook(script_path: str, tool_call: dict, cwd: str) -> tuple[str, str, int]:
    """Feed a tool-call JSON dict to a hook via stdin, return (stdout, stderr, rc)."""
    payload = json.dumps(tool_call)
    proc = subprocess.run(
        ["bash", script_path],
        input=payload,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return proc.stdout, proc.stderr, proc.returncode


def is_blocked(stdout: str) -> bool:
    """Check if a hook's stdout JSON indicates a block decision."""
    try:
        decision = json.loads(stdout)
        return decision.get("decision") == "block"
    except (json.JSONDecodeError, AttributeError):
        return False


def init_git_repo() -> str:
    repo = tempfile.mkdtemp(prefix="yishuship-e2e-")
    subprocess.run(["git", "init", "-q"], cwd=repo)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo)
    Path(repo, "README.md").write_text("seed\n")
    subprocess.run(["git", "add", "."], cwd=repo)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo)
    return repo


def setup_task_dir(repo: str, task_id: str = "test-task", phase: str = "design") -> Path:
    """Create .ship/tasks/<task_id>/ with current_phase file."""
    base = Path(repo) / ".ship" / "tasks" / task_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "current_phase").write_text(phase)
    return base


def make_agent_call(skill_name: str, cwd: str = "/tmp") -> dict:
    """Simulate a PreToolUse hook call for an Agent subagent invocation."""
    return {
        "tool_name": "Agent",
        "cwd": cwd,
        "tool_input": {
            "prompt": f"Run /yishuship:{skill_name} to implement the feature.",
            "subagent_type": "general-purpose",
        }
    }


# ── Test 1: pm-gate.sh blocks Agent calls without PM artifacts ──

class TestPmGateBlocksAgentCalls(unittest.TestCase):
    """pm-gate.sh intercepts Agent subagent invocations and blocks
    design/dev/auto calls when the V2 product handoff artifacts are missing."""

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def _setup_pm_state(self, task_id: str = "test-task") -> Path:
        """Create minimal PM workflow state."""
        task_dir = setup_task_dir(self.repo, task_id)
        pm_state = Path(self.repo) / ".ship" / "pm-state.yaml"
        pm_state.parent.mkdir(parents=True, exist_ok=True)
        pm_state.write_text(f"phase: product-spec\ntask_id: {task_id}\n")
        return task_dir

    def _create_v2_handoff(self, task_dir: Path):
        """Create all required V2 product handoff artifacts."""
        for f in ["00-product-type.json", "01-strategy.md", "03-problem-solution.md",
                   "08-prd.md", "09-tech-project-plan.md"]:
            (task_dir / "product" / f).parent.mkdir(parents=True, exist_ok=True)
            (task_dir / "product" / f).write_text("content\n")
        (task_dir / "delivery" / "design-spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "delivery" / "design-spec.md").write_text("content\n")
        (task_dir / "plan" / "spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "plan" / "spec.md").write_text("content\n")

    def test_blocks_design_agent_without_handoff(self):
        """Calling /yishuship:design agent should be blocked when no
        V2 product handoff artifacts exist."""
        self._setup_pm_state()
        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("design", self.repo),
            self.repo
        )
        self.assertTrue(is_blocked(stdout), f"Expected block, got stdout: {stdout}")

    def test_blocks_dev_agent_without_handoff(self):
        """Calling /yishuship:dev agent should be blocked without handoff."""
        self._setup_pm_state()
        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("dev", self.repo),
            self.repo
        )
        self.assertTrue(is_blocked(stdout))

    def test_blocks_auto_agent_without_handoff(self):
        """Calling /yishuship:auto agent should be blocked without handoff."""
        self._setup_pm_state()
        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("auto", self.repo),
            self.repo
        )
        self.assertTrue(is_blocked(stdout))

    def test_allows_non_agent_tool_calls(self):
        """Non-Agent tool calls (Read, Write, Bash) should pass through
        regardless of PM state."""
        self._setup_pm_state()
        for tool in ["Read", "Write", "Bash"]:
            stdout, stderr, rc = run_hook(
                GATE_SCRIPT,
                {"tool_name": tool, "input": {"file_path": "anything.txt"}},
                self.repo
            )
            self.assertFalse(is_blocked(stdout), f"{tool} should pass through")

    def test_passes_when_no_pm_state(self):
        """Without .ship/pm-state.yaml, all Agent calls should pass."""
        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("design", self.repo),
            self.repo
        )
        self.assertFalse(is_blocked(stdout))

    def test_passes_when_no_cwd(self):
        """Tool calls without cwd should pass (can't determine context)."""
        call = make_agent_call("design")
        call.pop("cwd", None)
        stdout, stderr, rc = run_hook(GATE_SCRIPT, call, self.repo)
        self.assertFalse(is_blocked(stdout))

    def test_allows_design_with_complete_handoff(self):
        """Design agent should be ALLOWED when all V2 handoff artifacts exist."""
        task_dir = self._setup_pm_state()
        self._create_v2_handoff(task_dir)

        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("design", self.repo),
            self.repo
        )
        self.assertFalse(is_blocked(stdout),
                         f"Complete handoff should allow design, got: {stdout}")


# ── Test 2: pm-verify.sh phase completion detection ──────────

class TestPmVerifyDetection(unittest.TestCase):
    """pm-verify.sh (V2) checks artifact existence for V2 phase names
    and blocks exit with a block JSON when artifacts are missing."""

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def _bogus_call(self, cwd: str = "/tmp") -> dict:
        return {"tool_name": "Read", "cwd": cwd, "input": {"file_path": "x"}}

    def _setup_pm_state(self, phase: str, task_id: str = "test-task"):
        pm_state = Path(self.repo) / ".ship" / "pm-state.yaml"
        pm_state.parent.mkdir(parents=True, exist_ok=True)
        pm_state.write_text(f"phase: {phase}\ntask_id: {task_id}\n")
        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def test_allows_exit_when_product_spec_complete(self):
        """product-spec phase with all required artifacts -> exit allowed."""
        task_dir = self._setup_pm_state("product-spec")
        for f in ["05-model-flow-role.md", "06-experience-spec.md",
                   "07-data-permission-analytics.md", "08-prd.md"]:
            (task_dir / "product" / f).parent.mkdir(parents=True, exist_ok=True)
            (task_dir / "product" / f).write_text("content\n")
        (task_dir / "plan" / "spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "plan" / "spec.md").write_text("content\n")

        stdout, stderr, rc = run_hook(VERIFY_SCRIPT, self._bogus_call(self.repo), self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(is_blocked(stdout), "Should not block when artifacts exist")

    def test_blocks_when_product_spec_artifacts_missing(self):
        """product-spec phase with missing artifacts -> block exit."""
        task_dir = self._setup_pm_state("product-spec")
        # Only create ONE of the required files
        (task_dir / "product" / "05-model-flow-role.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "product" / "05-model-flow-role.md").write_text("content\n")
        # 06, 07, 08, and spec.md are missing

        stdout, stderr, rc = run_hook(VERIFY_SCRIPT, self._bogus_call(self.repo), self.repo)
        self.assertTrue(is_blocked(stdout), "Should block when artifacts are missing")
        self.assertIn("缺失", stdout, "Block message should list missing items")

    def test_allows_exit_when_handoff_complete(self):
        """handoff phase with design-spec.md -> exit allowed."""
        task_dir = self._setup_pm_state("handoff")
        (task_dir / "delivery" / "design-spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "delivery" / "design-spec.md").write_text("content\n")

        stdout, stderr, rc = run_hook(VERIFY_SCRIPT, self._bogus_call(self.repo), self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(is_blocked(stdout))

    def test_passes_through_when_no_task_dir(self):
        stdout, stderr, rc = run_hook(VERIFY_SCRIPT, self._bogus_call(self.repo), self.repo)
        self.assertEqual(rc, 0)
        self.assertEqual(stderr.strip(), "")

    def test_unknown_phase_passes_through(self):
        """Unknown phase names (not in the case statement) -> allow exit."""
        self._setup_pm_state("some-unknown-phase")
        stdout, stderr, rc = run_hook(VERIFY_SCRIPT, self._bogus_call(self.repo), self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(is_blocked(stdout))


# ── Test 3: marker tampering resistance ──────────────────────

class TestMarkerTampering(unittest.TestCase):
    """An agent that modifies phase markers should still be caught by
    the orchestrator's artifact validation layer (defense in depth)."""

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def test_gate_bypass_via_pm_state_modification(self):
        """If an agent modifies pm-state.yaml to claim phase=complete,
        the pm-gate.sh still checks artifact existence, not just the phase string.
        This confirms the artifact-based gate is more robust than marker-based."""
        task_dir = setup_task_dir(self.repo)
        pm_state = Path(self.repo) / ".ship" / "pm-state.yaml"
        # Agent tampers: claims complete phase but no artifacts exist
        pm_state.write_text("phase: complete\ntask_id: test-task\n")

        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("design", self.repo),
            self.repo
        )
        # The gate checks for artifact FILES, not the phase string.
        # Without actual artifacts, it should still block.
        self.assertTrue(is_blocked(stdout),
                        "Tampered phase marker without artifacts should still be blocked")

    def test_gate_allows_with_artifacts_regardless_of_phase(self):
        """If all artifacts exist, the gate allows the call even if
        phase claims 'intake' -- artifact completeness is the truth."""
        task_dir = setup_task_dir(self.repo)
        pm_state = Path(self.repo) / ".ship" / "pm-state.yaml"
        pm_state.write_text("phase: intake\ntask_id: test-task\n")

        # Create all required V2 artifacts
        for f in ["00-product-type.json", "01-strategy.md", "03-problem-solution.md",
                   "08-prd.md", "09-tech-project-plan.md"]:
            (task_dir / "product" / f).parent.mkdir(parents=True, exist_ok=True)
            (task_dir / "product" / f).write_text("content\n")
        (task_dir / "delivery" / "design-spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "delivery" / "design-spec.md").write_text("content\n")
        (task_dir / "plan" / "spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "plan" / "spec.md").write_text("content\n")

        stdout, stderr, rc = run_hook(
            GATE_SCRIPT,
            make_agent_call("design", self.repo),
            self.repo
        )
        self.assertFalse(is_blocked(stdout),
                         "Complete artifacts should allow the call")


# ── Test 4: auto-orchestrate.sh state machine ────────────────

class TestOrchestratorStateMachine(unittest.TestCase):
    """auto-orchestrate.sh should correctly bootstrap a task and enforce
    phase transitions."""

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def test_init_creates_state_and_artifacts(self):
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "test feature"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0, f"init failed: {proc.stderr}")

        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        self.assertTrue(state.exists())
        content = state.read_text()
        self.assertIn("task_id:", content)
        self.assertIn("phase: pm_intake", content)
        self.assertIn("test feature", content)

    def test_init_creates_task_directory_with_subdirs(self):
        subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "test feature"],
            capture_output=True, text=True, cwd=self.repo
        )

        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        task_id = None
        for line in state.read_text().splitlines():
            if line.startswith("task_id:"):
                task_id = line.split(":", 1)[1].strip()
                break
        self.assertIsNotNone(task_id)

        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        for subdir in ["input", "product", "delivery", "control", "plan", "e2e", "qa"]:
            self.assertTrue(
                (task_dir / subdir).is_dir(),
                f"Subdir {subdir} should exist"
            )
        self.assertTrue((task_dir / "input" / "requirement.md").exists())

    def test_init_creates_feature_branch(self):
        subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "test feature"],
            capture_output=True, text=True, cwd=self.repo
        )
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=self.repo
        ).stdout.strip()
        self.assertTrue(branch.startswith("yishuship/"))

    def test_status_reports_active_task(self):
        subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "test feature"],
            capture_output=True, text=True, cwd=self.repo
        )
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "status"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("TASK_ID:", proc.stdout)
        self.assertIn("PHASE:", proc.stdout)

    def test_duplicate_init_is_rejected(self):
        subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "first"],
            capture_output=True, text=True, cwd=self.repo
        )
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "init", "second"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("Active task already exists", combined)

    def test_complete_without_state_fails(self):
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "complete", "design", "--verdict=success"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertNotEqual(proc.returncode, 0)


# ── Test 5: phase-guardrail.sh enforces phase isolation ──────

class TestPhaseGuardrail(unittest.TestCase):
    """phase-guardrail.sh blocks subagents from reading/writing artifacts
    from phases they shouldn't access."""

    def setUp(self):
        self.repo = init_git_repo()
        # Create state file for the guardrail to activate
        Path(self.repo, ".ship", "ship-auto.local.md").parent.mkdir(parents=True, exist_ok=True)
        Path(self.repo, ".ship", "ship-auto.local.md").write_text(
            "---\nactive: true\ntask_id: test-task\nphase: qa\n---\n"
        )
        # Create task dir with artifacts
        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "review.md").write_text("# Review findings\n")
        (task_dir / "plan.md").write_text("# Plan\n")

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def _subagent_call(self, tool: str, file_path: str) -> dict:
        return {
            "tool_name": tool,
            "agent_id": "test-subagent-1",
            "tool_input": {"file_path": file_path},
            "cwd": self.repo,
        }

    def test_qa_blocks_read_of_review_md(self):
        """In qa phase, subagent should not be able to read review.md."""
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Read",
                str(Path(self.repo) / ".ship" / "tasks" / "test-task" / "review.md")),
            self.repo
        )
        self.assertTrue(is_blocked(stdout), "QA should not read review.md")

    def test_qa_blocks_read_of_plan_md(self):
        """In qa phase, subagent should not be able to read plan.md."""
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Read",
                str(Path(self.repo) / ".ship" / "tasks" / "test-task" / "plan.md")),
            self.repo
        )
        self.assertTrue(is_blocked(stdout))

    def test_qa_blocks_write_to_source(self):
        """In qa phase, subagent should not write source code."""
        src_path = str(Path(self.repo) / "src" / "main.py")
        Path(src_path).parent.mkdir(parents=True, exist_ok=True)
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", src_path),
            self.repo
        )
        self.assertTrue(is_blocked(stdout))

    def test_review_blocks_write_to_source(self):
        """In review phase, subagent should not write source code."""
        # Update phase to review
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text("---\nactive: true\ntask_id: test-task\nphase: review\n---\n")

        src_path = str(Path(self.repo) / "src" / "main.py")
        Path(src_path).parent.mkdir(parents=True, exist_ok=True)
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", src_path),
            self.repo
        )
        self.assertTrue(is_blocked(stdout))

    def test_non_subagent_calls_pass_through(self):
        """Calls without agent_id should pass through (orchestrator is exempt)."""
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            {"tool_name": "Read", "tool_input": {"file_path": "anything.txt"}},
            self.repo
        )
        self.assertFalse(is_blocked(stdout))

    def test_no_state_file_passes_through(self):
        """Without state file, all calls pass."""
        Path(self.repo, ".ship", "ship-auto.local.md").unlink()
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Read", str(Path(self.repo) / "anything.txt")),
            self.repo
        )
        self.assertFalse(is_blocked(stdout))

    def test_qa_allows_own_artifact_writes(self):
        """QA phase subagent should be able to write its own artifacts."""
        qa_dir = Path(self.repo) / ".ship" / "tasks" / "test-task" / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", str(qa_dir / "report.md")),
            self.repo
        )
        self.assertFalse(is_blocked(stdout), "QA should be able to write its own artifacts")

    # ── Rule 5 tests: PM handoff gate ────────────────────────────

    def test_blocks_source_write_without_pm_handoff(self):
        """Subagent Write to source files should be blocked when PM handoff
        artifacts are missing -- this catches bypasses of pm-gate.sh."""
        # Set phase to 'dev' so Rule 3 (QA restriction) doesn't interfere
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text("---\nactive: true\ntask_id: test-task\nphase: dev\n---\n")

        # No PM artifacts created
        src_path = str(Path(self.repo) / "src" / "main.py")
        Path(src_path).parent.mkdir(parents=True, exist_ok=True)

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", src_path),
            self.repo
        )
        self.assertTrue(is_blocked(stdout), "Should block source write without PM handoff")
        self.assertIn("PM handoff", stdout, "Block message should mention PM handoff")

    def test_allows_source_write_with_pm_handoff(self):
        """Subagent Write to source files should be allowed when all PM handoff
        artifacts exist."""
        # Set phase to 'dev' so Rule 3 doesn't interfere
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text("---\nactive: true\ntask_id: test-task\nphase: dev\n---\n")

        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        # Create all required V2 handoff artifacts
        (task_dir / "product").mkdir(exist_ok=True)
        for f in ["00-product-type.json", "01-strategy.md", "03-problem-solution.md",
                   "08-prd.md", "09-tech-project-plan.md"]:
            (task_dir / "product" / f).write_text("content\n")
        (task_dir / "delivery").mkdir(exist_ok=True)
        (task_dir / "delivery" / "design-spec.md").write_text("content\n")
        (task_dir / "plan").mkdir(exist_ok=True)
        (task_dir / "plan" / "spec.md").write_text("content\n")

        src_path = str(Path(self.repo) / "src" / "main.py")
        Path(src_path).parent.mkdir(parents=True, exist_ok=True)

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", src_path),
            self.repo
        )
        self.assertFalse(is_blocked(stdout), "Should allow source write with complete PM handoff")

    def test_allows_edit_to_ship_metadata_without_pm_handoff(self):
        """Write/Edit to .ship/ paths should not be blocked by Rule 5
        (only source files require PM handoff)."""
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text("---\nactive: true\ntask_id: test-task\nphase: dev\n---\n")
        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", str(Path(self.repo) / ".ship" / "tasks" / "test-task" / "custom.md")),
            self.repo
        )
        # Rule 5 exempts *.ship/* paths
        self.assertFalse(is_blocked(stdout))

    def test_blocks_ship_metadata_write_when_checksum_mismatch(self):
        """Rule 6 should block .ship writes if a tracked control file was tampered."""
        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        (task_dir / "control").mkdir(parents=True, exist_ok=True)
        (task_dir / "control" / "run_state.yaml").write_text(
            "task_id: test-task\nphase: dev\n"
        )
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )

        update = subprocess.run(
            ["bash", f"{REPO_ROOT}/scripts/update-checksums.sh", "--init"],
            capture_output=True, text=True, cwd=self.repo,
        )
        self.assertEqual(update.returncode, 0, update.stderr)

        (task_dir / "control" / "run_state.yaml").write_text(
            "task_id: test-task\nphase: tampered\n"
        )

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", str(task_dir / "custom.md")),
            self.repo,
        )
        self.assertTrue(is_blocked(stdout), stdout)
        self.assertIn("artifact integrity", stdout)

    def test_blocks_edit_to_source_without_pm_handoff(self):
        """Rule 5 applies to Edit as well as Write."""
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text("---\nactive: true\ntask_id: test-task\nphase: dev\n---\n")
        src_path = str(Path(self.repo) / "src" / "main.py")
        Path(src_path).parent.mkdir(parents=True, exist_ok=True)

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Edit", src_path),
            self.repo
        )
        self.assertTrue(is_blocked(stdout), "Should block Edit to source without PM handoff")


# ── Test 6: stop-gate.sh (session exit guard) ─────────────────

class TestStopGate(unittest.TestCase):
    """stop-gate.sh blocks session exit when the external verifier
    determines the task is incomplete."""

    STOP_SCRIPT = f"{REPO_ROOT}/scripts/stop-gate.sh"

    def setUp(self):
        self.repo = init_git_repo()
        Path(self.repo, ".ship", "ship-auto.local.md").parent.mkdir(parents=True, exist_ok=True)
        Path(self.repo, ".ship", "ship-auto.local.md").write_text(
            '---\nactive: true\ntask_id: test-task\nphase: dev\nsession_id: sess-123\n---\nBuild a hello world app\n'
        )
        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        task_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def test_allows_exit_when_no_state(self):
        Path(self.repo, ".ship", "ship-auto.local.md").unlink()
        payload = json.dumps({"session_id": "sess-123", "cwd": self.repo})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0)

    def test_different_session_passes_through(self):
        """A different session should not be blocked (session isolation)."""
        payload = json.dumps({"session_id": "different-session", "cwd": self.repo})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0, "Different session should pass through")

    def test_no_cwd_passes_through(self):
        """Without cwd, the stop gate cannot evaluate."""
        payload = json.dumps({"session_id": "sess-123"})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0)

    def test_handoff_phase_with_pr_evidence_fast_path(self):
        """Handoff phase with PR evidence uses fast-path check.
        With PR evidence but no merge readiness, it should block quickly
        (no verifier call needed)."""
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        state.write_text(
            '---\nactive: true\ntask_id: test-task\nphase: handoff\nsession_id: sess-123\n---\n'
        )
        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "handoff.md").write_text(
            "PR URL: https://github.com/org/repo/pull/123\n"
        )

        payload = json.dumps({"session_id": "sess-123", "cwd": self.repo})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo,
            timeout=10
        )
        self.assertNotIn("Traceback", proc.stderr)
        # Should block because PR is not merge-ready (no real PR exists)
        self.assertTrue(is_blocked(proc.stdout))

    def test_dev_phase_times_out_instead_of_hanging(self):
        """Dev phase without a fast-path falls through to the verifier.
        The verifier may hang (codex/claude not responding), but the
        stop-gate should return within VERIFIER_TIMEOUT seconds with
        a block decision, not hang forever."""
        payload = json.dumps({"session_id": "sess-123", "cwd": self.repo})
        # Use a short timeout for the test -- the stop-gate's internal
        # VERIFIER_TIMEOUT is 30s, so 35s gives it time to time out
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo,
            timeout=35
        )
        # Should return (not hang) with a block decision
        self.assertNotEqual(proc.returncode, -9, "Should not be killed by timeout")
        self.assertTrue(
            is_blocked(proc.stdout) or "timeout" in proc.stdout.lower(),
            "Should block with timeout message when verifier hangs"
        )

    def test_verifier_task_complete_allows_exit_and_removes_state(self):
        """A successful external verifier should allow stop and remove state."""
        payload = json.dumps({"session_id": "sess-123", "cwd": self.repo})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo,
            env={
                **os.environ,
                "SHIP_AUTO_VERIFIER_CMD": "printf 'VERDICT: TASK_COMPLETE\\nSUMMARY: done\\n'",
                "SHIP_VERIFIER_TIMEOUT": "5",
            },
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertFalse(is_blocked(proc.stdout), proc.stdout)
        self.assertFalse(Path(self.repo, ".ship", "ship-auto.local.md").exists())

    def test_verifier_task_incomplete_blocks_with_missing_items(self):
        """A TASK_INCOMPLETE verifier verdict should block and preserve state."""
        payload = json.dumps({"session_id": "sess-123", "cwd": self.repo})
        proc = subprocess.run(
            ["bash", self.STOP_SCRIPT],
            input=payload, capture_output=True, text=True, cwd=self.repo,
            env={
                **os.environ,
                "SHIP_AUTO_VERIFIER_CMD": "printf 'VERDICT: TASK_INCOMPLETE\\nMISSING:\\n- run tests\\n'",
                "SHIP_VERIFIER_TIMEOUT": "5",
            },
            timeout=10,
        )
        self.assertTrue(is_blocked(proc.stdout), proc.stdout)
        self.assertIn("run tests", proc.stdout)
        self.assertTrue(Path(self.repo, ".ship", "ship-auto.local.md").exists())


# ── Test 7: Artifact format resilience ───────────────────────

class TestArtifactFormatResilience(unittest.TestCase):
    """Verify the system design choices that make artifacts resilient
    to agent drift and corruption."""

    def test_json_parse_fails_on_corruption(self):
        """JSON has stricter syntax: corruption causes parse failure,
        which is detectable by the orchestrator."""
        import json
        broken_json = '{"status": "DONE", "features": [{"name": "chat"}],}'
        with self.assertRaises(json.JSONDecodeError):
            json.loads(broken_json)

    def test_valid_json_passes_parse(self):
        import json
        valid = '{"status": "DONE", "features": [{"name": "chat"}]}'
        result = json.loads(valid)
        self.assertEqual(result["status"], "DONE")

# ── Test 9: Artifact integrity (SHA256 checksum validation) ────

class TestArtifactIntegrity(unittest.TestCase):
    """validate-artifacts.sh enforces SHA256 checksums on .ship control files.
    Blocks Write/Edit if checksums mismatch; allows on first run when no
    checksums exist; exempts non-.ship files."""

    VALIDATE_SCRIPT = f"{REPO_ROOT}/scripts/validate-artifacts.sh"
    UPDATE_SCRIPT = f"{REPO_ROOT}/scripts/update-checksums.sh"

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    def _run_check(self, repo: str) -> tuple[str, int]:
        proc = subprocess.run(
            ["bash", self.VALIDATE_SCRIPT, "--check", "--json"],
            capture_output=True, text=True, cwd=repo,
        )
        return proc.stdout.strip(), proc.returncode

    def _run_update(self, repo: str):
        proc = subprocess.run(
            ["bash", self.UPDATE_SCRIPT, "--init"],
            capture_output=True, text=True, cwd=repo,
        )
        self.assertEqual(proc.returncode, 0, f"update-checksums failed: {proc.stderr}")

    def _setup_ship_structure(self) -> str:
        """Create .ship structure with state file and one task dir."""
        task_id = "test-task"
        task_dir = setup_task_dir(self.repo, task_id)
        # Create control files that checksums will cover
        (task_dir / "control").mkdir(exist_ok=True)
        (task_dir / "control" / "run_state.yaml").write_text("status: active\nphase: design\n")
        (task_dir / "control" / "lifecycle-checklist.yaml").write_text("done: []\n")
        (task_dir / "handoff.md").write_text("# Handoff\n")
        return task_id

    def test_valid_state_passes(self):
        """When all tracked files match their stored checksums, --check exits 0
        and outputs an 'allow' block."""
        self._setup_ship_structure()
        # Write state file so validate-artifacts.sh picks up task_id
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )
        self._run_update(self.repo)

        stdout, rc = self._run_check(self.repo)
        self.assertEqual(rc, 0, f"Expected exit 0, got: {rc}, stdout: {stdout}")
        decision = json.loads(stdout)
        self.assertEqual(decision["decision"], "allow")

    def test_tampered_state_blocked(self):
        """When a tracked file is modified after checksum storage, --check
        exits 1 with a block JSON listing the tampered file."""
        self._setup_ship_structure()
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )
        self._run_update(self.repo)

        # Tamper: modify a tracked file
        run_state = Path(self.repo) / ".ship" / "tasks" / "test-task" / "control" / "run_state.yaml"
        run_state.write_text("status: TAMPERED\nphase: hacked\n")

        stdout, rc = self._run_check(self.repo)
        self.assertEqual(rc, 1, f"Expected exit 1, got: {rc}")
        decision = json.loads(stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertGreaterEqual(decision["count"], 1)
        # The tampered file should appear in mismatches
        paths = [m["path"] for m in decision["mismatches"]]
        self.assertTrue(
            any("run_state.yaml" in p for p in paths),
            f"run_state.yaml should be in mismatches: {paths}"
        )

    def test_task_scoped_check_ignores_other_task_mismatches(self):
        """--check --task <id> should ignore mismatches from other task dirs
        while still checking the selected task and global entries."""
        task_a = "task-a"
        task_b = "task-b"
        for task_id in [task_a, task_b]:
            task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
            (task_dir / "control").mkdir(parents=True, exist_ok=True)
            (task_dir / "control" / "run_state.yaml").write_text(
                f"task_id: {task_id}\nphase: design\n"
            )
            (task_dir / "input").mkdir(exist_ok=True)
            (task_dir / "input" / "idea.md").write_text(f"# {task_id}\n")
            (task_dir / "plan").mkdir(exist_ok=True)
            (task_dir / "plan" / "spec.md").write_text("# Spec\n")

        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: task-a\n"
        )
        self._run_update(self.repo)

        other_run_state = Path(self.repo) / ".ship" / "tasks" / task_b / "control" / "run_state.yaml"
        other_run_state.write_text("task_id: task-b\nphase: tampered\n")

        proc = subprocess.run(
            ["bash", self.VALIDATE_SCRIPT, "--check", "--task", task_a, "--json"],
            capture_output=True, text=True, cwd=self.repo,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(json.loads(proc.stdout)["decision"], "allow")

    def test_task_scoped_check_still_blocks_selected_task_mismatch(self):
        """--check --task <id> must still block mismatches inside that task."""
        task_id = self._setup_ship_structure()
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )
        self._run_update(self.repo)

        selected = Path(self.repo) / ".ship" / "tasks" / task_id / "control" / "run_state.yaml"
        selected.write_text("status: TAMPERED\n")

        proc = subprocess.run(
            ["bash", self.VALIDATE_SCRIPT, "--check", "--task", task_id, "--json"],
            capture_output=True, text=True, cwd=self.repo,
        )
        self.assertEqual(proc.returncode, 1)
        decision = json.loads(proc.stdout)
        self.assertEqual(decision["decision"], "block")
        paths = [m["path"] for m in decision["mismatches"]]
        self.assertTrue(any("test-task/control/run_state.yaml" in p for p in paths), paths)

    def test_missing_checksums_allowed_on_first_run(self):
        """When .checksums does not exist, --check should pass (bootstrap grace).
        No entries to verify = nothing to fail."""
        self._setup_ship_structure()
        # Do NOT run update-checksums; .checksums should not exist
        checksums_file = Path(self.repo) / ".ship" / ".checksums"
        self.assertFalse(checksums_file.exists(), ".checksums should not exist on first run")

        stdout, rc = self._run_check(self.repo)
        self.assertEqual(rc, 0, f"First run should pass, got: {rc}")
        decision = json.loads(stdout)
        self.assertEqual(decision["decision"], "allow")

    def test_non_ship_files_exempt(self):
        """Files outside .ship/* should not be tracked by the checksum system.
        Modifying a non-.ship file should not affect validate-artifacts.sh."""
        self._setup_ship_structure()
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )
        self._run_update(self.repo)

        # Modify a non-.ship file -- should not affect checksums
        readme = Path(self.repo) / "README.md"
        readme.write_text("modified by agent\n")

        stdout, rc = self._run_check(self.repo)
        self.assertEqual(rc, 0, f"Non-.ship changes should not block, got: {rc}")
        decision = json.loads(stdout)
        self.assertEqual(decision["decision"], "allow")



# ── Test 8: Cross-session resume ──────────────────────────────

class TestCrossSessionResume(unittest.TestCase):
    """auto-orchestrate.sh init -> partial progress -> complete ->
    resume must carry context from previous artifacts into the new session."""

    def setUp(self):
        self.repo = init_git_repo()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo])

    # ── helpers ────────────────────────────────────────────────

    def _stub_validate_artifacts(self):
        """Create a no-op validate-artifacts.sh so integrity checks pass
        in the temp test repo (the real script lives in the yishuship repo,
        not the temp repos we create here)."""
        scripts_dir = Path(self.repo) / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        stub = scripts_dir / "validate-artifacts.sh"
        stub.write_text(
            '#!/usr/bin/env bash\n'
            'case "$1" in\n'
            '  --check) exit 0;;\n'
            '  --update) exit 0;;\n'
            '  *) exit 0;;\n'
            'esac\n'
        )
        stub.chmod(0o755)

    def _init_task(self, description="cross-session test") -> str:
        """Init a task and return the extracted task_id."""
        self._stub_validate_artifacts()
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "init", description],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0, f"init failed: {proc.stderr}")
        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        for line in state.read_text().splitlines():
            if line.startswith("task_id:"):
                return line.split(":", 1)[1].strip()
        self.fail("task_id not found in state file")

    def _prompt_abs(self, prompt_file: str) -> Path:
        """Resolve the relative prompt path against the test repo."""
        p = Path(prompt_file)
        return p if p.is_absolute() else Path(self.repo) / p

    def _parse_kv_output(self, stdout: str) -> dict[str, str]:
        """Parse 'KEY:VALUE' lines from orchestrator output."""
        result = {}
        for line in stdout.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result

    def _write_pm_intake_artifacts(self, task_dir: Path):
        """Write all artifacts required for pm_intake -> design transition."""
        for f in ["00-product-type.json", "01-strategy.md", "02-research.md",
                   "03-problem-solution.md", "04-product-blueprint.md",
                   "05-model-flow-role.md", "06-experience-spec.md",
                   "07-data-permission-analytics.md", "08-prd.md",
                   "09-tech-project-plan.md"]:
            (task_dir / "product" / f).parent.mkdir(parents=True, exist_ok=True)
            (task_dir / "product" / f).write_text("content\n")
        (task_dir / "delivery" / "design-spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "delivery" / "design-spec.md").write_text("content\n")
        (task_dir / "control" / "lifecycle-checklist.yaml").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "control" / "lifecycle-checklist.yaml").write_text("content\n")
        (task_dir / "plan" / "spec.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "plan" / "spec.md").write_text(
            "# Spec\n\n## Acceptance Criteria\n- The feature must work\n"
        )

    def _complete_pm_intake(self, task_id: str) -> str:
        """Complete pm_intake phase -> advance to design. Returns PROMPT_FILE."""
        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        self._write_pm_intake_artifacts(task_dir)
        pm_state = Path(self.repo) / ".ship" / "pm-state.yaml"
        pm_state.write_text(f"task_id: {task_id}\nphase: complete\n")
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "complete", "pm_intake", "--verdict=success"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0,
                         f"complete pm_intake failed: {proc.stderr}\n{proc.stdout}")
        fields = self._parse_kv_output(proc.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "design")
        return fields["PROMPT_FILE"]

    def _write_design_artifacts(self, task_dir: Path):
        """Write design phase artifacts so complete design advances to dev."""
        plan_dir = task_dir / "plan"
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "spec.md").write_text(
            "# Spec\n\n## Acceptance Criteria\n\n- The feature must handle basic input\n"
            "- The system should validate responses\n"
        )
        (plan_dir / "plan.md").write_text(
            "# Plan\n\n## Tasks\n\n- Implement core logic\n- Add tests\n"
        )
        (plan_dir / "peer-spec.md").write_text("# Peer Spec\n\nReviewed and approved.\n")
        (plan_dir / "diff-report.md").write_text("# Diff Report\n\nNo divergence.\n")

    def _complete_design(self, task_id: str) -> str:
        """Complete design phase -> advance to dev. Returns PROMPT_FILE."""
        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        self._write_design_artifacts(task_dir)
        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "complete", "design", "--verdict=success"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(proc.returncode, 0,
                         f"complete design failed: {proc.stderr}\n{proc.stdout}")
        fields = self._parse_kv_output(proc.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "dev")
        return fields["PROMPT_FILE"]

    def _complete_dev(self, task_id: str) -> str:
        """Complete pm_intake -> design -> dev phases. Returns the dev prompt path."""
        self._complete_pm_intake(task_id)
        return self._complete_design(task_id)

    # ── tests ──────────────────────────────────────────────────

    def test_resume_after_dev_phase(self):
        """init -> complete pm_intake -> complete design -> resume dispatches
        to dev with correct task context from design artifacts."""
        task_id = self._init_task()
        self._complete_dev(task_id)

        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0,
                         f"resume failed: {resume_out.stderr}")
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "dev")

        prompt_file = fields["PROMPT_FILE"]
        self.assertTrue(self._prompt_abs(prompt_file).exists())
        prompt = self._prompt_abs(prompt_file).read_text()

        task_dir_str = f".ship/tasks/{task_id}"
        self.assertIn(task_dir_str, prompt,
                      "Prompt must reference the task directory")
        self.assertIn(f"{task_dir_str}/dev-context.md", prompt,
                      "Prompt must reference dev-context output path")
        self.assertIn(f"{task_dir_str}/plan/spec.md", prompt,
                      "Prompt must include spec artifact path")
        self.assertIn(f"{task_dir_str}/plan/plan.md", prompt,
                      "Prompt must include plan artifact path")
        self.assertIn("yishuship:dev", prompt,
                      "Prompt must dispatch to the dev skill")

    def test_resume_restores_phase_and_generates_prompt(self):
        """Resume after a partial session must return to the same phase
        and produce a non-empty prompt file."""
        task_id = self._init_task("resume phase test")
        self._complete_dev(task_id)

        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0,
                         f"resume failed: {resume_out.stderr}")
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "dev")
        self.assertNotEqual(fields.get("PROMPT_FILE", ""), "")
        self.assertTrue(self._prompt_abs(fields["PROMPT_FILE"]).exists())
        self.assertIn("Resuming", fields.get("MESSAGE", ""))

    def test_resume_after_review_fix_injects_findings(self):
        """Resume from review_fix phase must inject previous review findings
        into the new prompt via --findings-file."""
        task_id = self._init_task("review fix resume test")
        self._complete_dev(task_id)

        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        findings = "# P1: Auth token not validated\n# P2: Missing error handling\n"
        (task_dir / "review.md").write_text(findings)

        subprocess.run(
            ["bash", ORCH_SCRIPT, "complete", "review",
             "--verdict=findings", "--findings-file=review.md"],
            capture_output=True, text=True, cwd=self.repo
        )

        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0,
                         f"resume failed: {resume_out.stderr}")
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "review_fix")
        self.assertNotEqual(fields.get("PROMPT_FILE", ""), "")

        prompt = self._prompt_abs(fields["PROMPT_FILE"]).read_text()
        self.assertIn("Auth token not validated", prompt,
                      "Prompt must contain previous review findings")
        self.assertIn("Missing error handling", prompt,
                      "Prompt must contain second finding from review.md")
        self.assertIn("This is the FIX phase only", prompt,
                      "Prompt must identify the fix phase context")

    def test_resume_preserves_task_identity_across_phases(self):
        """After advancing through multiple phases and resuming, the prompt
        must consistently reference the same task_id."""
        task_id = self._init_task("identity preservation test")
        self._complete_dev(task_id)

        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0)
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        prompt = self._prompt_abs(fields["PROMPT_FILE"]).read_text()
        self.assertIn(task_id, prompt,
                      f"Prompt must contain task_id '{task_id}'")

    def test_resume_without_state_file_fails(self):
        """Calling resume when no state file exists should fail with an error."""
        subprocess.run(["bash", ORCH_SCRIPT, "init", "temp"],
                       capture_output=True, text=True, cwd=self.repo)
        Path(self.repo, ".ship", "ship-auto.local.md").unlink()

        proc = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_resume_checks_out_correct_branch(self):
        """Resume must git checkout the branch stored in state."""
        task_id = self._init_task("branch resume test")
        self._complete_dev(task_id)

        current = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=self.repo
        ).stdout.strip()
        self.assertNotEqual(current, "main")
        self.assertTrue(current.startswith("yishuship/"))

        subprocess.run(["git", "checkout", "main"],
                       capture_output=True, text=True, cwd=self.repo)

        subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        current_after = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=self.repo
        ).stdout.strip()
        self.assertEqual(current_after, current,
                         "Resume must checkout the feature branch")

    def test_init_creates_resumable_state(self):
        """After init, the state file must contain all fields that cmd_resume
        reads (task_id, phase, branch, session_id) and calling resume must
        succeed, dispatching back to pm_intake."""
        self._stub_validate_artifacts()
        task_id = self._init_task()

        state = Path(self.repo) / ".ship" / "ship-auto.local.md"
        content = state.read_text()
        # Frontmatter fields required by cmd_resume
        self.assertIn("task_id:", content)
        self.assertIn("phase: pm_intake", content)
        self.assertIn("branch:", content)
        self.assertIn("session_id:", content)
        # Fields required for full state machine resumption
        self.assertIn("scope_mode:", content)
        self.assertIn("started_at:", content)
        self.assertIn("pm_intake_retry_round: 0", content)
        self.assertIn("design_retry_round: 0", content)

        # Verify resume can read the state and dispatch
        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0,
                         f"resume failed on fresh state: {resume_out.stderr}")
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "pm_intake")

    def test_resume_after_partial_artifacts_references_existing_work(self):
        """Init -> write partial product artifacts -> simulate session end
        (state persists on disk) -> resume -> prompt references the
        artifact paths so the new session knows what already exists."""
        self._stub_validate_artifacts()
        task_id = self._init_task("cross-session resume test")

        # Step 3: write partial product artifacts (simulating work done in
        # a previous session before it ended)
        task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
        (task_dir / "product" / "00-product-type.json").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "product" / "00-product-type.json").write_text(
            '{"product_type":"web_app","name":"test-feature"}\n'
        )
        (task_dir / "product" / "01-strategy.md").parent.mkdir(parents=True, exist_ok=True)
        (task_dir / "product" / "01-strategy.md").write_text(
            "# Strategy\n\nTarget users: developers.\n"
        )

        # Step 4: "simulate session end" -- the state file already records
        # the current phase (pm_intake) on disk. Nothing to change; the file
        # persisting IS the session boundary.

        # Step 5: call resume
        resume_out = subprocess.run(
            ["bash", ORCH_SCRIPT, "resume"],
            capture_output=True, text=True, cwd=self.repo
        )
        self.assertEqual(resume_out.returncode, 0,
                         f"resume failed: {resume_out.stderr}")
        fields = self._parse_kv_output(resume_out.stdout)
        self.assertEqual(fields["ACTION"], "dispatch")
        self.assertEqual(fields["PHASE"], "pm_intake")

        # Step 6: verify the resumed prompt references the existing artifacts
        prompt_file = fields["PROMPT_FILE"]
        self.assertTrue(self._prompt_abs(prompt_file).exists(),
                        f"Prompt file should exist: {prompt_file}")
        prompt = self._prompt_abs(prompt_file).read_text()

        # The pm-intake template includes the full artifact paths in the
        # "Required artifacts" section via {{TASK_DIR}} substitution.
        task_dir_path = f".ship/tasks/{task_id}/product"
        self.assertIn(f"{task_dir_path}/00-product-type.json", prompt,
                      "Resumed prompt must list 00-product-type.json as required artifact")
        self.assertIn(f"{task_dir_path}/01-strategy.md", prompt,
                      "Resumed prompt must list 01-strategy.md as required artifact")
        # Also verify the prompt knows its own task identity
        self.assertIn(task_id, prompt,
                      "Resumed prompt must reference the task_id")
        self.assertIn(f"{task_dir_path}", prompt,
                      "Resumed prompt must reference the product artifact directory")

    def test_init_creates_task_prompts_directory(self):
        """Init should create the prompts/ subdirectory so resume can write
        the generated prompt file into it."""
        self._stub_validate_artifacts()
        task_id = self._init_task()
        prompts_dir = Path(self.repo) / ".ship" / "tasks" / task_id / "prompts"
        self.assertTrue(prompts_dir.is_dir(),
                        "prompts/ directory should exist after init")

        # The init-generated prompt should already be there
        self.assertTrue((prompts_dir / "pm-intake.md").exists(),
                        "pm-intake.md should be generated during init")


if __name__ == "__main__":
    unittest.main()
