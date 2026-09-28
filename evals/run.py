#!/usr/bin/env python3
"""Run yishuship's eval cases with `claude -p`, isolated from the user's own setup.

Why not `claude plugin eval`: on machines where it refuses Bash-granting runs
(for example a Docker credential store holding symlinks), this runner does the
same job. Cases use the same layout (prompt.md + graders/*.md), so the suite
stays portable; `command` graders are an extension it does not have.

Isolation for every run:
- only project/local settings load (no user CLAUDE.md, memory, skills, plugins);
- the plugin loads from a copy under /tmp, with --plugin-dir, in the with-arm only;
- YISHUSHIP_HOME points at a fresh folder, so the real registry is never touched;
- Bash runs in Claude Code's OS sandbox with the home folder unreadable and no
  way to run unsandboxed (permission rules alone miss chained shell commands);
- git uses a throwaway config, since ~/.gitconfig is unreadable in the sandbox;
- file-tool reads and writes under the real home folder, and git push, are denied;
- each run reports home-folder reads that were blocked, and flags any that got through.

Graders may set `group: target` for behaviors the plugin should have but may not
yet; the report scores `core` (current behavior) and `target` separately.

  python3 evals/run.py                      every case
  python3 evals/run.py --case 'shape-*'     cases matching a glob
  python3 evals/run.py --runs 1 -j 4        one run per arm, four at a time
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import datetime as dt
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "evals" / "cases"
REAL_HOME = str(Path.home())
TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "Skill", "TodoWrite", "Agent"]
SANDBOX = {"enabled": True, "allowUnsandboxedCommands": False, "failIfUnavailable": True,
           "filesystem": {"denyRead": ["~/"]}}


# ---------- case files ----------

def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    head, _, body = text[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if not sep or line.startswith(" "):
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        meta[key.strip()] = value
    return meta, body.strip()


def load_case(folder: Path) -> dict:
    meta, prompt = split_front_matter((folder / "prompt.md").read_text(encoding="utf-8"))
    graders = []
    for f in sorted((folder / "graders").glob("*.md")):
        g, body = split_front_matter(f.read_text(encoding="utf-8"))
        g["name"], g["body"] = f.stem, body
        graders.append(g)
    return {"name": folder.name, "dir": folder, "prompt": prompt, "meta": meta, "graders": graders,
            "scaffold": folder / "scaffold.sh" if (folder / "scaffold.sh").exists() else None}


# ---------- one run ----------

def snapshot(root: Path) -> dict[str, float]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and ".git" not in p.relative_to(root).parts:
            out[str(p.relative_to(root))] = p.stat().st_mtime_ns
    return out


def parse_trace(path: Path) -> dict:
    tool_calls, last, cost, error = [], "", 0.0, None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            for item in (d.get("message") or {}).get("content") or []:
                if item.get("type") == "tool_use":
                    tool_calls.append({"name": item.get("name"), "input": item.get("input")})
        if d.get("type") == "result":
            last = d.get("result") or ""
            cost = d.get("total_cost_usd") or 0.0
            if d.get("is_error") or d.get("subtype") not in (None, "success"):
                error = d.get("subtype")
    return {"tool_calls": tool_calls, "last_message": last, "cost": cost, "error": error}


def run_once(case: dict, arm: str, index: int, work: Path, args) -> dict:
    base = work / case["name"] / f"{arm}-{index}"
    ws, yshome = base / "ws", base / "yshome"
    ws.mkdir(parents=True)
    yshome.mkdir()
    (base / "gitconfig").write_text("[user]\n\tname = eval\n\temail = eval@example.com\n")
    outside = {k: v for k, v in os.environ.items() if not k.startswith("CMUX")}  # else `open` lands in the user's cmux pane
    env = dict(outside, YISHUSHIP_HOME=str(yshome), EVAL_WORKSPACE=str(ws), EVAL_PLUGIN=str(args.plugin_copy),
               GIT_CONFIG_GLOBAL=str(base / "gitconfig"), XDG_CONFIG_HOME=str(base),
               YISHUSHIP_NO_PAGE="1")  # no pages opening in the user's terminal during a run
    if case["scaffold"]:
        subprocess.run(["bash", str(case["scaffold"])], cwd=ws, env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    before = snapshot(ws)
    deny = [f"Read(/{REAL_HOME}/**)", f"Edit(/{REAL_HOME}/**)", f"Write(/{REAL_HOME}/**)",
            "Bash(git push:*)", "Bash(git push)"]
    cmd = ["claude", "-p", case["prompt"], "--output-format", "stream-json", "--verbose",
           "--model", args.model, "--max-turns", str(case["meta"].get("max_turns", 30)),
           "--setting-sources", "project,local", "--no-session-persistence",
           "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS,
           "--settings", json.dumps({"permissions": {"deny": deny}, "sandbox": {
               **SANDBOX, "filesystem": {**SANDBOX["filesystem"], "allowWrite": [str(yshome)]}}})]
    if arm == "with":
        cmd += ["--plugin-dir", str(args.plugin_copy)]
    trace = base / "trace.jsonl"
    timeout = int(case["meta"].get("timeout_seconds", 600))
    try:
        with trace.open("w") as out:
            subprocess.run(cmd, cwd=ws, env=env, stdout=out, stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL, timeout=timeout)
        run_error = None
    except subprocess.TimeoutExpired:
        run_error = f"timed out after {timeout}s"
    info = parse_trace(trace)
    after = snapshot(ws)
    info["created"] = sorted(set(after) - set(before))
    info["modified"] = sorted(k for k in set(after) & set(before) if after[k] != before[k])
    info["error"] = run_error or info["error"]
    info["trace_text"] = trace.read_text(encoding="utf-8", errors="ignore")
    info["env"] = env
    results = [grade(g, info, ws, args) for g in case["graders"]]

    def score_of(group):
        scored = [r for r in results if r["scored"](arm) and r["group"] == group]
        if not scored:
            return None
        return round(sum(r["weight"] for r in scored if r["passed"]) / sum(r["weight"] for r in scored), 3)
    score, target = score_of("core"), score_of("target")
    attempts, leaked = home_access(trace)
    return {"arm": arm, "index": index, "score": score if score is not None else 0.0, "target": target,
            "cost": info["cost"],
            "error": info["error"], "isolation_leak": leaked, "blocked_home_reads": attempts,
            "workspace": str(ws), "trace": str(trace),
            "graders": [{k: v for k, v in r.items() if k != "scored"} for r in results]}


def home_access(trace: Path) -> tuple[int, bool]:
    """(tool calls that reached for the real home folder, whether any of them got through).

    Every such call should come back denied; one that does not is a leak and
    makes the run's score untrustworthy.
    """
    calls, silenced, attempts, leaked = {}, {}, 0, False
    home = re.compile(re.escape(REAL_HOME) + r"/|~/")
    for line in trace.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            msg = json.loads(line).get("message")
        except ValueError:
            continue
        if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        for item in msg["content"]:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":  # text written into files is not a read
                calls[item["id"]] = item.get("name") not in ("Write", "Edit", "TodoWrite") and bool(
                    home.search(json.dumps(item.get("input"), ensure_ascii=False)))
                command = (item.get("input") or {}).get("command", "") if item.get("name") == "Bash" else ""
                parts = [p for p in re.split(r"&&|\|\||;|\n", command) if home.search(p)]
                silenced[item["id"]] = bool(parts) and all(re.search(r"2>\s*/dev/null", p) for p in parts)
            elif item.get("type") == "tool_result" and calls.get(item.get("tool_use_id")):
                attempts += 1
                if silenced.get(item.get("tool_use_id")):
                    continue  # its stderr went to /dev/null, so a denial leaves no text; the sandbox still denied it
                text = json.dumps(item.get("content"), ensure_ascii=False)
                if not re.search(r"denied|blocked by a deny rule|Permission to|Operation not permitted", text):
                    leaked = True
    return attempts, leaked


# ---------- graders ----------

def target_text(target: str, info: dict, ws: Path) -> str:
    if target in ("", "last_message"):
        return info["last_message"]
    if target == "trace":
        return info["trace_text"]
    if target == "files":
        return "\n".join(info["created"])
    if target.startswith("file:"):
        matches = sorted(ws.glob(target[5:]))
        return "\n\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in matches if p.is_file())
    raise ValueError(f"unknown target {target}")


def judge(criteria: str, text: str, args) -> tuple[bool, str]:
    prompt = ("You are grading one output against a rubric. Reply with exactly one line: "
              "PASS: <one-sentence reason> or FAIL: <one-sentence reason>.\n\n"
              f"<rubric>\n{criteria}\n</rubric>\n\n<output>\n{text[:30000]}\n</output>")
    votes = []
    for _ in range(3):
        r = subprocess.run(["claude", "-p", prompt, "--model", args.judge_model, "--max-turns", "1",
                            "--setting-sources", "project,local", "--no-session-persistence", "--tools", ""],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300,
                           cwd=tempfile.gettempdir())
        line = (r.stdout.strip().splitlines() or ["FAIL: no answer"])[-1]
        votes.append((line.upper().startswith("PASS"), line))
    passed = sum(v for v, _ in votes) >= 2
    return passed, next(line for v, line in votes if v == passed)


def grade(g: dict, info: dict, ws: Path, args) -> dict:
    kind, weight = g.get("type"), float(g.get("weight", 1))
    arm_rule = g.get("arm", "")
    passed, why = False, ""
    try:
        if kind == "regex":
            text = target_text(g.get("target", ""), info, ws)
            flags = re.I if "i" in g.get("flags", "") else 0
            found = re.findall(g["pattern"], text, flags | re.M)
            match = g.get("match", "contains")
            if match == "not_contains":
                passed, why = not found, f"{len(found)} match(es), expected none"
            elif match.startswith("count:"):
                passed, why = len(found) == int(match[6:]), f"{len(found)} match(es)"
            else:
                passed, why = bool(found), f"{len(found)} match(es)"
        elif kind == "tool_used":
            pattern = g.get("input_match")
            n = sum(1 for c in info["tool_calls"] if c["name"] == g["tool"] and
                    (not pattern or re.search(pattern, json.dumps(c["input"], ensure_ascii=False))))
            lo, hi = int(g.get("min", 1)), int(g.get("max", 10**9))
            passed, why = lo <= n <= hi, f"{n} call(s), wanted {lo}..{hi if hi < 10**9 else '∞'}"
        elif kind == "file_exists":
            hits = [f for f in info["created"] if fnmatch.fnmatch(f, g["path"])]
            want = str(g.get("exists", "true")).lower() != "false"
            passed, why = bool(hits) == want, f"created: {hits[:5] or 'none'}"
        elif kind == "command":
            r = subprocess.run(["bash", "-c", g["body"]], cwd=ws, env=info["env"],
                               capture_output=True, text=True, timeout=120)
            passed = r.returncode == 0
            why = (r.stdout + r.stderr).strip()[-300:] or f"exit {r.returncode}"
        elif kind == "llm":
            passed, why = judge(g["body"], target_text(g.get("focus", ""), info, ws), args)
        else:
            why = f"unknown grader type {kind}"
    except Exception as e:  # a broken grader fails, visibly
        passed, why = False, f"grader error: {e}"
    return {"name": g["name"], "type": kind, "weight": weight, "passed": passed, "why": why,
            "group": g.get("group", "core"),
            "scored": lambda arm: not (arm_rule == "with-only")}


# ---------- suite ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="*")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("-j", "--concurrency", type=int, default=4)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--judge-model", default="claude-sonnet-5")
    ap.add_argument("--arms", choices=["auto", "with", "both"], default="auto",
                    help="auto: baseline only for cases tagged natural")
    args = ap.parse_args()

    cases = [load_case(d) for d in sorted(CASES.iterdir())
             if (d / "prompt.md").exists() and fnmatch.fnmatch(d.name, args.case)]
    if not cases:
        print("no cases", file=sys.stderr)
        return 1
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    work = Path(tempfile.gettempdir()) / f"ys-eval-{stamp}"
    args.plugin_copy = work / "plugin" / "yishuship"
    shutil.copytree(REPO, args.plugin_copy, ignore=shutil.ignore_patterns(".git", "evals", ".ship", "__pycache__"))
    out_dir = REPO / "evals" / "results" / stamp
    out_dir.mkdir(parents=True)

    jobs = []
    for case in cases:
        arms = ["with"]
        if args.arms == "both" or (args.arms == "auto" and "natural" in case["meta"].get("tags", [])):
            arms.append("without")
        jobs += [(case, arm, i) for arm in arms for i in range(1, args.runs + 1)]
    print(f"{len(cases)} case(s), {len(jobs)} run(s), model {args.model}, judge {args.judge_model}")
    print(f"workspaces: {work}")

    results: dict[str, list] = {c["name"]: [] for c in cases}
    with futures.ThreadPoolExecutor(args.concurrency) as pool:
        pending = {pool.submit(run_once, c, a, i, work, args): (c["name"], a, i) for c, a, i in jobs}
        for f in futures.as_completed(pending):
            name, arm, i = pending[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"arm": arm, "index": i, "score": 0.0, "cost": 0, "error": f"runner error: {e}",
                     "isolation_leak": False, "graders": []}
            results[name].append(r)
            fails = [g["name"] for g in r["graders"] if not g["passed"]]
            flag = "  ISOLATION LEAK" if r.get("isolation_leak") else (
                f"  ({r['blocked_home_reads']} home read(s) blocked)" if r.get("blocked_home_reads") else "")
            print(f"  {name} {arm}-{i}: {r['score']:.2f}  ${r['cost']:.2f}  "
                  f"{'fail: ' + ', '.join(fails) if fails else 'all pass'}{' · ' + r['error'] if r.get('error') else ''}{flag}")

    summary = []
    for case in cases:
        runs = sorted(results[case["name"]], key=lambda r: (r["arm"], r["index"]))
        mean = lambda arm: (lambda xs: round(sum(xs) / len(xs), 2) if xs else None)(
            [r["score"] for r in runs if r["arm"] == arm])
        w, wo = mean("with"), mean("without")
        tw = (lambda xs: round(sum(xs) / len(xs), 2) if xs else None)(
            [r["target"] for r in runs if r["arm"] == "with" and r.get("target") is not None])
        summary.append({"case": case["name"], "description": case["meta"].get("description", ""),
                        "with": w, "without": wo, "target": tw, "delta": round(w - wo, 2) if wo is not None else None,
                        "cost": round(sum(r["cost"] for r in runs), 2), "runs": runs})
    (out_dir / "results.json").write_text(json.dumps(
        {"model": args.model, "judge": args.judge_model, "plugin_version": json.loads(
            (REPO / ".claude-plugin" / "plugin.json").read_text())["version"], "cases": summary},
        ensure_ascii=False, indent=2))
    write_report(summary, out_dir / "report.md", args)
    for d in (Path(REAL_HOME) / ".claude" / "projects").glob(f"*ys-eval-{stamp}*"):
        # Claude Code itself writes oversized tool output (<session>/tool-results/) and subagent
        # metadata (<session>/subagents/) here; anything else stays and is reported.
        if any(p.is_file() and not {"tool-results", "subagents"} & set(p.parts) for p in d.rglob("*")):
            print(f"note: {d} is not empty; left in place")
        else:
            shutil.rmtree(d)

    print(f"\n{'CASE':22} CORE  W/OUT  Δ      TARGET  COST")
    for s in summary:
        fmt = lambda v, sign=False: "  -  " if v is None else (f"{v:+.2f}" if sign else f"{v:.2f}")
        print(f"{s['case']:22} {fmt(s['with'])}  {fmt(s['without'])}  {fmt(s['delta'], True)}  "
              f"{fmt(s['target'])}   ${s['cost']:.2f}")
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    print(f"\ncore {avg([s['with'] for s in summary if s['with'] is not None]):.2f} · "
          f"target {avg([s['target'] for s in summary if s['target'] is not None]):.2f} · "
          f"cost ${sum(s['cost'] for s in summary):.2f}")
    print(f"report: {out_dir / 'report.md'}")
    return 0


def write_report(summary: list, path: Path, args) -> None:
    lines = [f"# yishuship eval · {path.parent.name}", "",
             f"model `{args.model}` · judge `{args.judge_model}`", "",
             "| case | core | without | Δ | target | cost |", "|---|---|---|---|---|---|"]
    dash = lambda v: "-" if v is None else v
    for s in summary:
        lines.append(f"| {s['case']} | {s['with']} | {dash(s['without'])} | {dash(s['delta'])} | "
                     f"{dash(s['target'])} | ${s['cost']} |")
    for s in summary:
        lines += ["", f"## {s['case']}", "", s["description"], ""]
        for r in s["runs"]:
            head = f"### {r['arm']}-{r['index']} · core {r['score']} · target {r.get('target')}"
            if r.get("error"):
                head += f" · {r['error']}"
            if r.get("isolation_leak"):
                head += " · ISOLATION LEAK"
            lines += [head, f"workspace `{r.get('workspace', '')}`", ""]
            for g in r["graders"]:
                tag = " · target" if g.get("group") == "target" else ""
                lines.append(f"- {'✓' if g['passed'] else '✗'} **{g['name']}** ({g['type']}{tag}): {g['why']}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
