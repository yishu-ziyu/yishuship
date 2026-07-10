#!/usr/bin/env python3
"""Activation Layer tests: detect → enter → run_state disk facts.

Contract: docs/decisions/DEC-0005-activation-contract.md

Run:
  python3 benchmarks/test_activation_layer.py -v
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / "scripts" / "yishuship-bootstrap.sh"


def init_git_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="yishuship-activation-"))
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def run_bootstrap(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # Invoke bootstrap with cwd=repo so REPO_ROOT resolves to the temp git root.
    # The script lives in the real yishuship repo; we call it by absolute path.
    env = os.environ.copy()
    return subprocess.run(
        ["bash", str(BOOTSTRAP), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def parse_kv(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        if ": " not in line:
            # also allow "key:value"
            m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
            if not m:
                continue
            out[m.group(1)] = m.group(2).strip()
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


class ActivationLayerTests(unittest.TestCase):
    def test_bootstrap_script_exists_and_executable(self) -> None:
        self.assertTrue(BOOTSTRAP.is_file(), str(BOOTSTRAP))
        self.assertTrue(os.access(BOOTSTRAP, os.X_OK), "bootstrap should be executable")

    def test_status_without_enablement_is_idle(self) -> None:
        repo = init_git_repo()
        proc = run_bootstrap(repo, "status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        kv = parse_kv(proc.stdout)
        self.assertEqual(kv.get("enabled"), "false")
        self.assertEqual(kv.get("active_task"), "none")
        self.assertEqual(kv.get("phase"), "none")
        self.assertEqual(kv.get("next_action"), "idle")
        self.assertIn("sense_where", kv)
        self.assertIn("sense_report", kv)
        self.assertIn("【现在】", kv.get("sense_report", ""))

    def test_status_with_enabled_marker_routes(self) -> None:
        repo = init_git_repo()
        ship = repo / ".ship"
        ship.mkdir(parents=True)
        (ship / "enabled").write_text("", encoding="utf-8")

        proc = run_bootstrap(repo, "status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        kv = parse_kv(proc.stdout)
        self.assertEqual(kv.get("enabled"), "true")
        self.assertEqual(kv.get("active_task"), "none")
        self.assertEqual(kv.get("next_action"), "route")
        self.assertIn("enter", kv.get("sense_next", "").lower() + kv.get("sense_report", "").lower())

    def test_status_with_config_enabled_false_is_bypass_ok(self) -> None:
        repo = init_git_repo()
        ship = repo / ".ship"
        ship.mkdir(parents=True)
        (ship / "config.yaml").write_text("enabled: false\n", encoding="utf-8")

        proc = run_bootstrap(repo, "status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        kv = parse_kv(proc.stdout)
        self.assertEqual(kv.get("enabled"), "false")
        self.assertEqual(kv.get("next_action"), "bypass_ok")

    def test_enter_creates_run_state_when_enabled(self) -> None:
        repo = init_git_repo()
        ship = repo / ".ship"
        ship.mkdir(parents=True)
        (ship / "config.yaml").write_text("enabled: true\n", encoding="utf-8")

        proc = run_bootstrap(repo, "enter", "add activation smoke test")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        kv = parse_kv(proc.stdout)
        task_id = kv.get("task_id")
        self.assertTrue(task_id, f"missing task_id in: {proc.stdout!r}")
        self.assertNotEqual(task_id, "none")

        run_state = repo / ".ship" / "tasks" / task_id / "control" / "run_state.yaml"
        self.assertTrue(run_state.is_file(), f"expected {run_state}")
        body = run_state.read_text(encoding="utf-8")
        self.assertIn(f"task_id: {task_id}", body)
        self.assertIn("active: true", body)
        self.assertIn("current_phase:", body)
        self.assertIn("status: running", body)

        status = run_bootstrap(repo, "status")
        self.assertEqual(status.returncode, 0, status.stderr)
        skv = parse_kv(status.stdout)
        self.assertEqual(skv.get("enabled"), "true")
        self.assertEqual(skv.get("active_task"), task_id)
        self.assertEqual(skv.get("next_action"), "resume")
        self.assertTrue(skv.get("sense_next"), "sense_next required")
        self.assertTrue(skv.get("sense_effect"), "sense_effect required")
        self.assertTrue(skv.get("sense_presentation"), "sense_presentation required")
        self.assertTrue(skv.get("sense_preview"), "sense_preview required")
        report = skv.get("sense_report", "")
        self.assertIn("【现在】", report)
        self.assertIn("【做完后】", report)
        self.assertIn("【先感受】", report)

    def test_status_sense_for_review_phase(self) -> None:
        repo = init_git_repo()
        task_id = "sense-review-task"
        control = repo / ".ship" / "tasks" / task_id / "control"
        product = repo / ".ship" / "tasks" / task_id / "product"
        delivery = repo / ".ship" / "tasks" / task_id / "delivery"
        plan = repo / ".ship" / "tasks" / task_id / "plan"
        e2e = repo / ".ship" / "tasks" / task_id / "e2e"
        for d in (control, product, delivery, plan, e2e):
            d.mkdir(parents=True)
        (control / "run_state.yaml").write_text(
            "\n".join(
                [
                    f"task_id: {task_id}",
                    "active: true",
                    "current_phase: review",
                    "status: running",
                    'updated_at: "2026-07-10T00:00:00Z"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (product / "00-product-type.json").write_text('{"product_type":"C"}\n', encoding="utf-8")
        (product / "08-prd.md").write_text("# PRD\n\nseams\n", encoding="utf-8")
        (delivery / "design-spec.md").write_text("# design\n", encoding="utf-8")
        (plan / "spec.md").write_text("# spec\n", encoding="utf-8")
        (plan / "plan.md").write_text("# plan\n", encoding="utf-8")
        (e2e / "report.md").write_text("# e2e ok\n", encoding="utf-8")

        proc = run_bootstrap(repo, "status")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        kv = parse_kv(proc.stdout)
        self.assertEqual(kv.get("phase"), "review")
        self.assertEqual(kv.get("next_action"), "resume")
        self.assertIn("review", kv.get("sense_next", ""))
        self.assertIn("pm_handoff", kv.get("sense_have", ""))
        # Causal chain required (no naked next step)
        self.assertTrue(kv.get("sense_effect"))
        self.assertTrue(kv.get("sense_presentation"))
        self.assertTrue(kv.get("sense_preview"))

    def test_enter_reuses_active_task(self) -> None:
        repo = init_git_repo()
        task_id = "existing-task"
        control = repo / ".ship" / "tasks" / task_id / "control"
        control.mkdir(parents=True)
        (control / "run_state.yaml").write_text(
            "\n".join(
                [
                    f"task_id: {task_id}",
                    "active: true",
                    "current_phase: design",
                    "status: running",
                    'updated_at: "2026-07-10T00:00:00Z"',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        proc = run_bootstrap(repo, "enter", "should reuse")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        kv = parse_kv(proc.stdout)
        self.assertEqual(kv.get("task_id"), task_id)
        self.assertEqual(kv.get("action"), "reuse")
        # Must not invent a second task root.
        tasks = list((repo / ".ship" / "tasks").iterdir())
        self.assertEqual(len(tasks), 1)

    def test_session_start_injects_yishuship_status(self) -> None:
        # Run session-start from a temp enabled repo by copying bootstrap
        # resolution: session-start uses SCRIPT_DIR for bootstrap, so we
        # only assert the real script emits the status tags when bootstrap
        # works in the current yishuship checkout.
        session_start = REPO_ROOT / "scripts" / "session-start.sh"
        self.assertTrue(session_start.is_file())
        proc = subprocess.run(
            ["bash", str(session_start)],
            input="{}",
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # With jq present, stdout is JSON wrapping additionalContext.
        self.assertIn("YISHUSHIP_STATUS", proc.stdout)
        self.assertIn("YISHUSHIP_STATE_SENSE", proc.stdout)
        self.assertIn("next_action", proc.stdout)
        self.assertIn("enabled", proc.stdout)
        self.assertIn("sense_report", proc.stdout)


if __name__ == "__main__":
    unittest.main()
