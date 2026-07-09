# Long-Horizon Workflow Hardening Implementation Plan

> **For agentic workers:** Use /yishuship:dev to implement this plan task by task.
> Steps use checkbox syntax for tracking.

**Goal:** Finish the yishuship long-horizon workflow hardening slice by fixing checksum task-scope behavior, stop-gate verifier parsing, historical YAML doc drift, and generated cache noise.

**Architecture:** Keep the shell scripts as deep modules with small CLI or hook JSON interfaces.
`validate-artifacts.sh` owns manifest filtering and checksum decisions.
`stop-gate.sh` owns session-exit verifier behavior.
The benchmark suite tests those public seams rather than private helper details.

**Tech Stack:** Bash, jq, Python unittest through pytest, git, yishuship `.ship` artifacts.

---

### Task 0: Verify the active PM handoff and design transition

**Files:**
- Inspect: `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/product/`
- Inspect: `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/control/run_state.yaml`
- Inspect: `.ship/pm-state.yaml`

- [ ] **Step 1: Verify active PM handoff artifacts exist**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

task = "continue-yishuship-transformation-work-after-migrating-produ"
base = Path(".ship/tasks") / task
required = [
    "product/00-product-type.json",
    "product/01-strategy.md",
    "product/02-research.md",
    "product/03-problem-solution.md",
    "product/04-product-blueprint.md",
    "product/05-model-flow-role.md",
    "product/06-experience-spec.md",
    "product/07-data-permission-analytics.md",
    "product/08-prd.md",
    "product/09-tech-project-plan.md",
    "control/lifecycle-checklist.yaml",
    "delivery/design-spec.md",
    "plan/spec.md",
]
missing = [path for path in required if not (base / path).is_file() or (base / path).stat().st_size == 0]
if missing:
    raise SystemExit(f"missing or empty artifacts: {missing}")

state = Path(".ship/pm-state.yaml").read_text()
run_state = (base / "control/run_state.yaml").read_text()
assert f"task_id: {task}" in state, state
assert "phase: complete" in state, state
assert "current_phase: design" in run_state, run_state
print("active PM handoff is complete and auto advanced to design")
PY
```

Expected: prints `active PM handoff is complete and auto advanced to design`.

- [ ] **Step 2: Verify orchestrator state is in design**

Run:

```bash
scripts/auto-orchestrate.sh status
```

Expected: output includes `TASK_ID:continue-yishuship-transformation-work-after-migrating-produ` and `PHASE:design`.

---

### Task 1: Add regression tests for task-scoped checksum filtering and checksum guardrail blocking

**Files:**
- Modify: `benchmarks/test_long_horizon_e2e.py:422-603`
- Modify: `benchmarks/test_long_horizon_e2e.py:718-827`
- Modify later: `scripts/validate-artifacts.sh:55-127`

- [ ] **Step 1: Write failing tests for task-scoped checksum checks**

Add these methods inside `TestArtifactIntegrity` after `test_tampered_state_blocked`.

```python
    def test_task_scoped_check_ignores_other_task_mismatches(self):
        """--check --task <id> should ignore mismatches from other task dirs
        while still checking the selected task and global entries."""
        task_a = "task-a"
        task_b = "task-b"
        for task_id in [task_a, task_b]:
            task_dir = Path(self.repo) / ".ship" / "tasks" / task_id
            (task_dir / "control").mkdir(parents=True, exist_ok=True)
            (task_dir / "control" / "run_state.yaml").write_text(f"task_id: {task_id}\nphase: design\n")
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
```

- [ ] **Step 2: Write a failing guardrail test for checksum mismatch blocking**

Add this method inside `TestPhaseGuardrail` after `test_allows_edit_to_ship_metadata_without_pm_handoff`.

```python
    def test_blocks_ship_metadata_write_when_checksum_mismatch(self):
        """Rule 6 should block .ship writes if a tracked control file was tampered."""
        task_dir = Path(self.repo) / ".ship" / "tasks" / "test-task"
        (task_dir / "control").mkdir(parents=True, exist_ok=True)
        (task_dir / "control" / "run_state.yaml").write_text("task_id: test-task\nphase: dev\n")
        Path(self.repo, ".ship", "pm-state.yaml").write_text(
            "phase: complete\ntask_id: test-task\n"
        )

        update = subprocess.run(
            ["bash", f"{REPO_ROOT}/scripts/update-checksums.sh", "--init"],
            capture_output=True, text=True, cwd=self.repo,
        )
        self.assertEqual(update.returncode, 0, update.stderr)

        (task_dir / "control" / "run_state.yaml").write_text("task_id: test-task\nphase: tampered\n")

        stdout, stderr, rc = run_hook(
            GUARDRAIL_SCRIPT,
            self._subagent_call("Write", str(task_dir / "custom.md")),
            self.repo,
        )
        self.assertTrue(is_blocked(stdout), stdout)
        self.assertIn("artifact integrity", stdout)
```

- [ ] **Step 3: Run focused tests and verify the new checksum task-scope test fails**

Run:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestArtifactIntegrity benchmarks/test_long_horizon_e2e.py::TestPhaseGuardrail -v --tb=short
```

Expected: `test_task_scoped_check_ignores_other_task_mismatches` fails before implementation.
The guardrail checksum test may pass already if Rule 6 is wired correctly.

- [ ] **Step 4: Implement task filtering in `validate-artifacts.sh`**

In `do_check()`, before resolving each manifest key, skip entries that belong to a different task directory.
Keep global entries such as `.ship/pm-state.yaml` and `.ship/ship-auto.local.md` checked.
Use this helper near the top of `do_check()` after option parsing.

```bash
  should_check_manifest_key() {
    local key="$1"
    [ -z "$task_id" ] && return 0

    case "$key" in
      .ship/tasks/*)
        local rest task_key
        rest="${key#.ship/tasks/}"
        task_key="${rest%%/*}"
        [ "$task_key" = "$task_id" ]
        return $?
        ;;
      *)
        return 0
        ;;
    esac
  }
```

Then add this guard immediately inside the manifest loop before resolving `{task_id}`.

```bash
    should_check_manifest_key "$key" || continue
```

- [ ] **Step 5: Run the focused tests and verify they pass**

Run:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestArtifactIntegrity benchmarks/test_long_horizon_e2e.py::TestPhaseGuardrail -v --tb=short
```

Expected: all selected tests pass.

---

### Task 2: Add regression tests for normal stop-gate verifier verdicts

**Files:**
- Modify: `benchmarks/test_long_horizon_e2e.py:606-695`
- Modify later: `scripts/stop-gate.sh:330-397`

- [ ] **Step 1: Write failing tests for TASK_COMPLETE and TASK_INCOMPLETE**

Add `import os` near the top of `benchmarks/test_long_horizon_e2e.py` with the other imports.

Add these methods inside `TestStopGate` after `test_dev_phase_times_out_instead_of_hanging`.

```python
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
```

- [ ] **Step 2: Run the focused stop-gate tests and verify they fail**

Run:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestStopGate -v --tb=short
```

Expected: the new verdict tests fail before implementation because `stop-gate.sh` parses the old temp file path instead of the captured verifier text.

- [ ] **Step 3: Fix stop-gate parsing to use `VERIFIER_CONTENT`**

In `scripts/stop-gate.sh`, replace the verdict and section parsing variables after the verifier output is read.

Replace:

```bash
VERDICT=$(verdict_line "$VERIFIER_OUTPUT")
```

with:

```bash
VERDICT=$(verdict_line "$VERIFIER_CONTENT")
```

Replace:

```bash
BLOCKER=$(extract_section "BLOCKER:" "$VERIFIER_OUTPUT")
```

with:

```bash
BLOCKER=$(extract_section "BLOCKER:" "$VERIFIER_CONTENT")
```

Replace:

```bash
MISSING=$(extract_section "MISSING:" "$VERIFIER_OUTPUT")
```

with:

```bash
MISSING=$(extract_section "MISSING:" "$VERIFIER_CONTENT")
```

Replace the invalid-verdict output interpolation:

```bash
Verifier output:
$VERIFIER_OUTPUT"
```

with:

```bash
Verifier output:
$VERIFIER_CONTENT"
```

- [ ] **Step 4: Run stop-gate tests and verify they pass**

Run:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py::TestStopGate -v --tb=short
```

Expected: all `TestStopGate` tests pass.

---

### Task 3: Mark old YAML-first superpowers docs as historical snapshots

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md:1`
- Modify: `docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md:1`

- [ ] **Step 1: Add a short historical notice to both docs**

At the top of each file, add this note after the first heading or before the first section.
Do not rewrite the whole doc, because these files are dated design records.

```markdown
> Historical note: this 2026-06-29 snapshot predates the JSON migration.
> The current canonical lifecycle entry artifact for new work is `product/00-product-type.json`; legacy `product/00-product-type.yaml` is migration fallback only.
> See `skills/.shared/product-lifecycle-21.md` for the current protocol.
```

- [ ] **Step 2: Verify active new-task instructions are JSON-first**

Run:

```bash
rg -n "00-product-type\.yaml" skills scripts benchmarks docs .ship/tasks/20260701-yishuship-sync-infra .ship/tasks/continue-yishuship-transformation-work-after-migrating-produ
```

Expected: hits in `scripts/pm-gate.sh`, `scripts/pm-verify.sh`, and `scripts/phase-guardrail.sh` are compatibility logic.
Hits in the two superpowers docs are historical snapshot content with a top-of-file note.
No active skill prompt, shared protocol, or generated `/yishuship:auto` prompt tells new tasks to write YAML.

---

### Task 4: Clean generated cache noise and refresh integrity baseline

**Files:**
- Restore if generated-only: `benchmarks/__pycache__/pm_scorer.cpython-313.pyc`
- Update after all intentional `.ship` changes: `.ship/.checksums`

- [ ] **Step 1: Confirm the modified `.pyc` file is generated cache noise**

Run:

```bash
git status --short -- benchmarks/__pycache__/pm_scorer.cpython-313.pyc
git diff --numstat -- benchmarks/__pycache__/pm_scorer.cpython-313.pyc
```

Expected: the path is under `benchmarks/__pycache__/` and the diff is binary or non-human source.
If the path is not generated cache, stop and ask before restoring.

- [ ] **Step 2: Restore the generated Python cache file from git**

Run only after Step 1 confirms generated cache noise:

```bash
git restore benchmarks/__pycache__/pm_scorer.cpython-313.pyc
```

Expected: `git status --short -- benchmarks/__pycache__/pm_scorer.cpython-313.pyc` prints nothing.

- [ ] **Step 3: Re-baseline `.ship` integrity manifest after all legitimate `.ship` changes are complete**

Run this after Tasks 0 through 3 are complete, not before.

```bash
bash scripts/update-checksums.sh --init
bash scripts/validate-artifacts.sh --check --json
```

Expected: `validate-artifacts.sh` prints `{"decision":"allow", ...}`.

---

### Task 5: Run full regression verification

**Files:**
- Test: `benchmarks/test_long_horizon_e2e.py`
- Test: `benchmarks/`
- Inspect: `.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/`

- [ ] **Step 1: Re-run active handoff verification**

Run the same Python snippet from Task 0 Step 1.

Expected: prints `active PM handoff is complete and auto advanced to design`.

- [ ] **Step 2: Run targeted long-horizon E2E suite**

Run:

```bash
python3 -m pytest benchmarks/test_long_horizon_e2e.py -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 3: Run full benchmark suite**

Run:

```bash
python3 -m pytest benchmarks/ -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 4: Run checksum validation once more**

Run:

```bash
bash scripts/validate-artifacts.sh --check --json
```

Expected: allow decision.

- [ ] **Step 5: Verify active instruction sources are JSON-first**

Run:

```bash
rg -n "00-product-type\.yaml" skills/.shared skills/pm-intake skills/auto/prompts skills/use-yishuship
```

Expected: no output.

- [ ] **Step 6: Inspect final working tree**

Run:

```bash
git status --short
```

Expected: all changed paths are either pre-existing intentional changes from this branch or one of the paths below:

```text
.ship/.checksums
.ship/pm-state.yaml
.ship/tasks/20260701-yishuship-sync-infra/delivery/design-spec.md
.ship/tasks/20260701-yishuship-sync-infra/product/00-product-type.yaml
.ship/tasks/20260701-yishuship-sync-infra/product/00-product-type.json
.ship/tasks/continue-yishuship-transformation-work-after-migrating-produ/
CONTEXT.md
benchmarks/test_long_horizon_e2e.py
docs/superpowers/plans/2026-06-29-yishuship-v2-lifecycle.md
docs/superpowers/specs/2026-06-29-yishuship-v2-lifecycle-design.md
scripts/auto-orchestrate.sh
scripts/phase-guardrail.sh
scripts/pm-gate.sh
scripts/pm-verify.sh
scripts/stop-gate.sh
scripts/update-checksums.sh
scripts/validate-artifacts.sh
skills/.shared/product-lifecycle-21.md
skills/auto/prompts/pm-intake.md.tmpl
skills/pm-intake/SKILL.md
skills/use-yishuship/SKILL.md
```

Any other changed path is a fail unless the implementer can tie it directly to this plan.
Generated `.pyc` changes are absent.

---

## Self-Review

Spec coverage: every acceptance criterion in `plan/spec.md` maps to Tasks 0 through 5.
Placeholder scan: no placeholder steps remain.
Type consistency: script names and test class names match current files.
Anti-shortcut check: the plan requires behavior tests before script fixes and does not allow satisfying tests by weakening hooks or removing checksum enforcement.
