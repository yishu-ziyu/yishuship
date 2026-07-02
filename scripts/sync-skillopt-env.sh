#!/usr/bin/env bash
set -euo pipefail

SKILLOPT_ROOT="${1:-${SKILLOPT_ROOT:-/tmp/SkillOpt}}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_ENV="$REPO_ROOT/benchmarks/skillopt-env"
SRC_DATA="$REPO_ROOT/benchmarks/yishuship_split"

if [[ ! -f "$SKILLOPT_ROOT/scripts/train.py" || ! -d "$SKILLOPT_ROOT/skillopt/envs" ]]; then
  echo "SkillOpt root not found or incomplete: $SKILLOPT_ROOT" >&2
  echo "Clone https://github.com/microsoft/SkillOpt.git, then rerun this script." >&2
  exit 1
fi

ENV_DIR="$SKILLOPT_ROOT/skillopt/envs/yishuship"
CONFIG_DIR="$SKILLOPT_ROOT/configs/yishuship"
DATA_DIR="$SKILLOPT_ROOT/data/yishuship_split"

mkdir -p "$ENV_DIR/prompts" "$ENV_DIR/skills" "$CONFIG_DIR"
cp "$SRC_ENV/__init__.py" "$ENV_DIR/__init__.py"
cp "$SRC_ENV/adapter.py" "$ENV_DIR/adapter.py"
cp "$SRC_ENV/dataloader.py" "$ENV_DIR/dataloader.py"
cp "$SRC_ENV/rollout.py" "$ENV_DIR/rollout.py"
cp "$REPO_ROOT/benchmarks/pm_scorer.py" "$ENV_DIR/pm_scorer.py"
cp "$REPO_ROOT/benchmarks/matt_flow_scorer.py" "$ENV_DIR/matt_flow_scorer.py"
cp "$SRC_ENV/initial.md" "$ENV_DIR/skills/initial.md"
cp "$SRC_ENV/analyst_error.md" "$ENV_DIR/prompts/analyst_error.md"
cp "$SRC_ENV/analyst_success.md" "$ENV_DIR/prompts/analyst_success.md"
cp "$SRC_ENV/default.yaml" "$CONFIG_DIR/default.yaml"
rm -rf "$DATA_DIR"
mkdir -p "$(dirname "$DATA_DIR")"
cp -R "$SRC_DATA" "$DATA_DIR"

patch_registry() {
  local target="$1"
  python3 - "$target" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "skillopt.envs.yishuship.adapter" in text:
    raise SystemExit(0)

anchor = "\n\ndef get_adapter"
if anchor not in text:
    raise SystemExit(f"Cannot find get_adapter anchor in {path}")

block = """
    try:
        from skillopt.envs.yishuship.adapter import YishushipAdapter
        _ENV_REGISTRY["yishuship"] = YishushipAdapter
    except ImportError:
        pass
"""

path.write_text(text.replace(anchor, block + anchor, 1), encoding="utf-8")
PY
}

patch_registry "$SKILLOPT_ROOT/scripts/train.py"
patch_registry "$SKILLOPT_ROOT/scripts/eval_only.py"

echo "Synced yishuship SkillOpt env into: $SKILLOPT_ROOT"
echo
echo "Smoke check:"
echo "  python3 -m py_compile skillopt/envs/yishuship/*.py"
echo
echo "Baseline eval:"
echo "  python scripts/eval_only.py --config configs/yishuship/default.yaml --skill skillopt/envs/yishuship/skills/initial.md --split test"
echo
echo "Train:"
echo "  python scripts/train.py --config configs/yishuship/default.yaml"
