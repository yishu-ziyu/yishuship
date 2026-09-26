#!/usr/bin/env bash
# Install yishuship for Claude Code from this checkout. Safe to run again.
#
#   bash scripts/install.sh                  plugin + status line; asks about Obsidian
#   bash scripts/install.sh --obsidian DIR   also link progress files into an Obsidian folder
#   bash scripts/install.sh --no-obsidian    never ask about Obsidian
#   bash scripts/install.sh --no-statusline  leave ~/.claude/settings.json alone
#
# Before changing ~/.claude/settings.json it saves a copy next to it.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
obsidian="" ask_obsidian=1 statusline=1
while [ $# -gt 0 ]; do
  case "$1" in
    --obsidian) obsidian="${2:?--obsidian needs a folder}"; ask_obsidian=0; shift 2 ;;
    --no-obsidian) ask_obsidian=0; shift ;;
    --no-statusline) statusline=0; shift ;;
    *) sed -n '2,9p' "$0" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null || { echo "需要 python3" >&2; exit 1; }
command -v claude >/dev/null || { echo "需要先装 Claude Code：https://code.claude.com" >&2; exit 1; }

echo "1/3 安装插件"
claude plugin marketplace add "$root" >/dev/null </dev/null
claude plugin install yishuship@yishuship >/dev/null </dev/null
echo "    已装好 yishuship@yishuship（来自 ${root}）"

echo "2/3 底部状态行"
if [ "$statusline" = 1 ]; then
  python3 - "$root" <<'EOF'
import datetime, json, re, shlex, shutil, sys
from pathlib import Path

root = sys.argv[1]
ours = f"bash {shlex.quote(root + '/scripts/statusline.sh')}"
path = Path.home() / ".claude" / "settings.json"
settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
existing = (settings.get("statusLine") or {}).get("command", "").strip()

# Keep whatever status line was there; yishuship adds its line below it.
if "/scripts/statusline.sh" in existing:  # ours from an earlier install, maybe another path
    existing = existing.split("/scripts/statusline.sh", 1)[1].lstrip("'\"").strip()
if not existing:
    command = ours
elif existing.startswith("sh -c ") or not re.search(r"[|;&<>$`()]", existing):
    command = f"{ours} {existing}"
else:
    command = f"{ours} sh -c {shlex.quote(existing)}"

if (settings.get("statusLine") or {}).get("command") == command:
    print("    已经接好，没有改动")
    sys.exit()
if path.exists():
    backup = path.with_name(f"settings.json.bak-yishuship-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(path, backup)
    print(f"    原文件备份在 {backup}")
settings["statusLine"] = {"type": "command", "command": command}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("    已接好" + ("，原来的状态行照常显示在上面" if existing else ""))
EOF
else
  echo "    跳过"
fi

echo "3/3 Obsidian（可选）"
if [ "$ask_obsidian" = 1 ] && [ -t 0 ]; then
  printf "    想在 Obsidian 里看进度文件吗？输入库里的一个文件夹路径，直接回车跳过：\n    > "
  read -r obsidian || true
fi
if [ -n "$obsidian" ]; then
  obsidian="${obsidian/#\~/$HOME}"
  yshome="${YISHUSHIP_HOME:-$HOME/.yishuship}"
  mkdir -p "$yshome" "$obsidian"
  config="$yshome/config"
  { [ -f "$config" ] && grep -v '^obsidian_dir=' "$config" || true; echo "obsidian_dir=$obsidian"; } > "$config.tmp"
  mv "$config.tmp" "$config"
  python3 "$root/scripts/ideas.py" --link-all >/dev/null
  echo "    已设置：${obsidian}（以后登记的项目会自动连过去）"
else
  echo "    跳过（进度文件就在各项目的 .ship/ideas/ 里，任何编辑器都能看）"
fi

cat <<EOF

装好了。接下来：
  1. 推荐同时装 Waza 的四个技能（查报错、出方案、review、读网页）：
     npx skills add tw93/Waza -s hunt think check read -g -y -a claude-code
  2. 重开 Claude Code，进到你的项目里，打：
     /yishuship 一句话说你的想法
EOF
