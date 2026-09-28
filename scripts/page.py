#!/usr/bin/env python3
"""A page beside the terminal: does the user need to act, what the agent is doing and for what, what comes next;
below it, the project as a whole from .ship/PROJECT.md.

  page.py DIR           open the page for the project containing DIR; reuses the
                        one already open, reopens it if the user closed it
  page.py --html DIR    print the page once (for checking)
  page.py --serve ROOT  run the local server (started by the first form)

YISHUSHIP_NO_PAGE=1 turns opening off (the eval runner sets it).

The server renders from the progress file on every request, so the page follows
whatever the agent writes. The page asks again every 2 seconds; once nobody has
asked for IDLE_EXIT seconds the server exits on its own.
"""
from __future__ import annotations

import hashlib
import math
import mimetypes
import html
import http.server
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ideas import (_section, current, doing, done_slices, evidence_note, project_file, project_root, questions, quiet_for,  # noqa: E402
                   slice_names, slice_things, trace, visuals)

POLL_MS = 2000
IDLE_EXIT = 600      # seconds without a request before the server stops
CLOSED_AFTER = 8     # seconds without a request before the page counts as closed


# ---------- reading the progress file ----------

def waiting_block(idea: dict) -> str:
    """The question saved under ## 等你决定, when the user owes a decision."""
    if not idea.get("waiting"):
        return ""
    text = Path(idea["file"]).read_text(encoding="utf-8")
    section = re.search(r"^## 等你决定\n(.*?)(?=^#{1,2} |\Z)", text, flags=re.M | re.S)
    text = section.group(1) if section else ""
    fence = re.search(r"```[^\n]*\n(.*?)```", text, flags=re.S)
    block = fence.group(1).rstrip() if fence else (text.strip() or idea["waiting"])  # an unfenced block still counts
    return re.sub(r"\A\[yishuship\] *需要你决定\s*\n", "", block).strip("\n")  # the page already says it


# ---------- drawing it ----------
# Three questions, most urgent first: do I need to do anything; what is it doing
# and for what; what happens next. Normal is quiet; only exceptions stand out.

def esc(text: str) -> str:
    return html.escape(text or "")


def body(root: Path) -> str:
    idea = current(str(root))
    return main_body(idea) + (trace_view(idea) if idea else "") + project_view(root)


def project_view(root: Path) -> str:
    """The project as a whole, from .ship/PROJECT.md: what it is, can do, is building, still owes."""
    file = project_file(root)
    if not file.exists():
        return ""
    text = file.read_text(encoding="utf-8")
    items = lambda name: [m.group(1).strip() for m in re.finditer(r"^- (.+)$", _section(text, name), flags=re.M)]
    plain = lambda name: re.sub(r"<!--.*?-->", "", _section(text, name), flags=re.S).strip()

    def column(title: str, rows: list[str], empty: str, show: int = 8) -> str:
        cells = []
        for row in rows:
            split = re.search(r" · (来自「.*)$", row)  # generated rows end with where they came from
            main, rest = (row[:split.start()], split.group(1)) if split else row.partition(" · ")[::2]
            rest = re.sub(r"\[([^\]]+)\]\([^)]+\)", "", rest).strip(" ·")
            cells.append(f'<li>{inline(main)}{f"<div class=sub>{esc(rest)}</div>" if rest else ""}</li>')
        more = (f'<details><summary>还有 {len(cells) - show} 条</summary><ul>{"".join(cells[show:])}</ul></details>'
                if len(cells) > show else "")
        return (f'<div class="blk"><h3>{title}</h3><div class="cnt">{len(rows)}</div>'
                f'<ul class="pl">{"".join(cells[:show]) or f"<li class=none>{empty}</li>"}</ul>{more}</div>')

    what = plain("这是什么")
    built = plain("怎么搭的")
    fence = re.search(r"```[^\n]*\n(.*?)```", built, flags=re.S)
    built_html = f"<pre>{esc(fence.group(1).rstrip())}</pre>" if fence else (f"<p>{inline(built)}</p>" if built else "")
    screens = ""
    for row in items("界面现在长什么样"):
        found = re.search(r"screens/[^\s·)]+", row)
        ref = found.group(0) if found else ""
        label = re.sub(r"\s*·?\s*" + re.escape(ref) + r"\s*·?\s*", " · ", row).strip(" ·") if ref else row
        target = root / ".ship" / ref
        if ref.endswith(".txt") and target.is_file():
            media = f"<pre class=out>{esc(target.read_text(encoding='utf-8', errors='replace').rstrip())}</pre>"
        elif ref and target.is_file():
            media = f'<div class="fig" data-box=""><img src="/{esc(ref)}" alt=""></div>'
        else:
            media = '<div class="nopic">没有截图</div>'
        screens += f'<div class="scr">{media}<div class="kind">{esc(label)}</div></div>'
    return (f'<section class="proj"><p class="which">项目 · {esc(root.name)}</p>'
            + (f'<p class="what">{inline(what)}</p>' if what else "")
            + '<div class="cols">'
            + column("现在能做什么", items("现在能做什么"), "还没有被证据证明过的行为")
            + column("想法", items("想法"), "还没有想法")
            + column("待办和技术债", items("待办和技术债"), "无")
            + "</div>"
            + (f'<h3 class="oq">怎么搭的</h3>{built_html}' if built_html else "")
            + (f'<h3 class="oq">界面现在长什么样</h3><div class="opts">{screens}</div>' if screens else "")
            + "</section>")


def main_body(idea: dict | None) -> str:
    if idea is None:
        return '<p class="state">这个项目现在没有进行中的想法</p>'
    kind = "bug · " if idea.get("kind") == "bug" else ""
    top = f'<p class="which">{esc(idea.get("project"))} · {kind}{esc(idea.get("idea"))}</p>'
    slice_name = idea.get("slice", "")
    question = waiting_block(idea)
    if question:
        where = f'<p class="quiet">停在：{esc(slice_name)}</p>' if slice_name else ""
        seen = visuals(idea)
        return (f'{top}<p class="state alert">需要你决定</p>{where}<pre>{with_terms(question, seen["terms"])}</pre>'
                f'{option_cards(seen["options"])}<p class="quiet">在终端里回复</p>')
    step, thing, place, _ = doing(idea)
    working, age = bool(idea.get("now")), quiet_for(idea) if idea.get("now") else ""
    found = questions(idea)
    if found:
        return top + unknowns(idea, found, agent_line(idea, step, thing, working, age))
    if age:
        head = (f'<p class="state alert">⚠ {esc(age.removesuffix("前"))}没有动静</p>'
                '<p class="quiet">可能卡住了，或者会话已经关了。在终端里打 /yishuship 看看</p>')
    elif working:
        head = f'<p class="state">不用管它<span class="quiet"> · {esc(minutes_ago(idea))}更新</span></p>'
    else:
        head = ('<p class="state">现在没有 Agent 在做</p>'
                '<p class="quiet">要它接着做，在终端里打 /yishuship</p>')
    now = ""
    if working:
        what = f"{esc(step)}：{esc(thing)}" if thing else esc(step)
        if age:  # it may have stopped: say where it was, not that it is still going
            what = "上次" + ("" if step.startswith("在") else "在") + what
        now = f'<p class="now">{what}</p>'
    things = slice_things(idea)
    rows = "".join(
        f'<li class="{"done" if done else ("here" if n == place else "")}">'
        f'<span class="mark">{"✓" if done else ("◐" if n == place else "○")}</span>{esc(text)}</li>'
        for n, (done, text) in enumerate(things, 1))
    listing = (f'<p class="label list">{esc(slice_name)} · {len(things)} 件事</p><ul>{rows}</ul>' if things else "")
    after = ("" if age or not idea.get("next")
             else f'<p class="next"><span class="label">接下来</span>{esc(idea.get("next"))}</p>')
    return f"{top}{head}{now}{listing}{after}"


def trace_view(idea: dict) -> str:
    """Each behavior with what serves and proves it; a behavior nothing proves stands out."""
    t = trace(idea)
    if not t["behaviors"] or not any(b["designs"] or b["slices"] or b["proven_by"] for b in t["behaviors"]):
        return ""
    cell = lambda xs, none: "".join(f"<div>{esc(x)}</div>" for x in xs) or f'<div class="none">{none}</div>'
    rows = ""
    for b in t["behaviors"]:
        missing = b["built"] and not b["proven_by"]
        proof = cell(b["proven_by"], "做完了，没有证据" if missing else ("还没做" if b["slices"] else "—"))
        rows += (f'<tr class="{"gap" if missing else ""}"><td><b>{esc(b["id"])}</b> {esc(b["text"])}'
                 f'<div class="dec">{"定了" if b["decided"] else "待定"}</div></td>'
                 f'<td>{cell(b["designs"], "—")}</td><td>{cell(b["slices"], "—")}</td><td>{proof}</td></tr>')
    gaps = "".join(f"<li>{esc(g)}</li>" for g in t["gaps"])
    return (f'<h3 class="oq">需求怎么落到设计、任务和证据</h3><table class="trace"><tr><th>用户能看到的行为</th><th>设计</th>'
            f'<th>任务</th><th>被什么证明</th></tr>{rows}</table>'
            + (f'<details class="gaps"><summary>断开的地方 · {len(t["gaps"])}</summary><ul>{gaps}</ul></details>' if gaps else ""))


def figure(item: dict, cls: str = "fig") -> str:
    """A picture with the thing it points at boxed; the box is placed once the image loads."""
    box = ",".join(map(str, item["box"])) if item.get("box") else ""
    return (f'<div class="{cls}" data-box="{box}"><img src="{esc(item["src"])}" alt=""><i class="box"></i></div>'
            if item.get("src") else "")


def with_terms(block: str, terms: list[dict]) -> str:
    """The question as written, with every named thing that has a picture underlined: hover to see it."""
    text = esc(block)
    marks = {}
    for n, term in enumerate(sorted((t for t in terms if t.get("src")), key=lambda t: -len(t["word"]))):
        key = f"\x00{n}\x00"
        marks[key] = (f'<span class="term" data-src="{esc(term["src"])}" data-box="{",".join(map(str, term["box"] or []))}"'
                      f' data-what="{esc(term["what"])}">{esc(term["word"])}</span>')
        text = text.replace(esc(term["word"]), key)
    for key, span in marks.items():
        text = text.replace(key, span)
    return text


def option_cards(groups: list[dict]) -> str:
    """Each option of each question side by side: what the product looks like or does under it."""
    out = ""
    for group in groups:
        cards = ""
        for o in group["opts"]:
            if o["src"].endswith(".html"):
                media = (f'<div class="frame" data-src="{esc(o["src"])}"><iframe src="{esc(o["src"])}" sandbox loading="lazy"></iframe>'
                         '<i class="cover"></i></div>')
            else:
                media = figure(o) or f'<div class="nopic">没有图</div>'
            cards += (f'<div class="opt{" rec" if o["rec"] else ""}"><div class="oh">{esc(o["letter"])} {esc(o["label"])}'
                      f'{"<em>◀ 推荐</em>" if o["rec"] else ""}</div><div class="looks">{esc(o["looks"])}</div>'
                      f'{media}<div class="kind">{esc(o["kind"])}</div></div>')
        out += f'<h3 class="oq">{esc(group["q"])}</h3><div class="opts">{cards}</div>'
    return out


def agent_line(idea: dict, step: str, thing: str, working: bool, age: str) -> str:
    if age:
        return f'<p class="agent alert">⚠ Agent {esc(age.removesuffix("前"))}没有动静，可能卡住了。在终端里打 /yishuship 看看</p>'
    if working:
        return f'<p class="agent">Agent {esc(step)}{"：" + esc(thing) if thing else ""}<span class="quiet"> · {esc(minutes_ago(idea))}</span></p>'
    return '<p class="agent quiet">现在没有 Agent 在做，要它接着做就在终端里打 /yishuship</p>'


def top_ask(found: list[dict]) -> tuple[str, int]:
    """Of the open questions only the user can close, the action that closes the most."""
    counts: dict[str, int] = {}
    for q in found:
        if not q["closed"] and q["ask"]:
            counts[q["ask"]] = counts.get(q["ask"], 0) + 1
    return max(counts.items(), key=lambda kv: kv[1]) if counts else ("", 0)


def unknowns(idea: dict, found: list[dict], agent: str) -> str:
    """One sentence on what needs the user, a hill placed by closed/all per slice, the questions by slice.

    The sentence is counted from ## 问题, never written by hand; a closed question with a
    `### <question>` note under ## 证据 opens that note one level down."""
    slices, done, names = list(dict.fromkeys(q["slice"] for q in found)), done_slices(idea), slice_names(idea)
    ask, closes = top_ask(found)
    clauses = []
    for name in slices:
        mine = [q for q in found if q["slice"] == name and not q["closed"] and q["ask"] != ask]
        if mine:
            who = "Agent 在试" if all(not q["ask"] for q in mine) else "有的要你来"
            clauses.append(f"{name or '其余'}还有 {len(mine)} 个没想清楚，{who}")
    still = sum(not q["closed"] for q in found)
    say = (f'要你<mark>{esc(ask)}</mark>，能关掉 {closes} 个问题。' if ask else "")
    say += (f'<span class="g">{esc("；".join(clauses))}。</span>' if clauses else "")
    say = say or '问题都关掉了，只剩照着做。'
    # the hill: uphill share = closed / all; a slice only goes downhill once it is ticked off in 进度
    W, base, high, x0 = 1000, 40 + 22 * len(slices) + 60, 60, 20
    point = lambda x: (x0 + x / 100 * (W - 2 * x0), base - high * math.sin(math.pi * x / 100))
    path = " ".join(f'{"L" if x else "M"}{point(x)[0]:.1f} {point(x)[1]:.1f}' for x in range(0, 101, 2))
    marks = ""
    for n, name in enumerate(slices):
        mine = [q for q in found if q["slice"] == name]
        shut = sum(q["closed"] for q in mine)
        x = 100 if name in done and shut == len(mine) else shut / len(mine) * 50
        cx, cy = point(x)
        ly, anchor = 16 + n * 22, "start" if x < 15 else "end" if x > 85 else "middle"
        marks += (f'<line x1="{cx:.1f}" y1="{ly + 5}" x2="{cx:.1f}" y2="{cy - 9:.1f}" stroke="#d8d2c5"/>'
                  f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="{"#1b1b1a" if shut == len(mine) else "#f4f1ea"}" stroke="#1b1b1a" stroke-width="1.6"/>'
                  f'<text x="{cx:.1f}" y="{ly}" text-anchor="{anchor}">{esc(name or "这个想法")} · 关掉 {shut}/{len(mine)}</text>')
    hill = (f'<svg class="hill" viewBox="0 0 {W} {base + 30}"><path d="{path}" fill="none" stroke="#cfc8ba" stroke-width="1.5"/>'
            f'<line x1="{W / 2}" y1="{base - high}" x2="{W / 2}" y2="{base + 8}" stroke="#ddd6c8" stroke-dasharray="3 4"/>{marks}'
            f'<text class="axis" x="{x0}" y="{base + 26}">← 上坡：还有问题开着</text>'
            f'<text class="axis" x="{W / 2}" y="{base - high - 8}" text-anchor="middle">问题全关掉</text>'
            f'<text class="axis" x="{W - x0}" y="{base + 26}" text-anchor="end">下坡：只剩照着做 →</text></svg>')
    cols = ""
    for name in slices:
        mine = [(i, q) for i, q in enumerate(found) if q["slice"] == name]
        shut = sum(q["closed"] for _, q in mine)
        rows = "".join(f'<div class="q open"><div class="t">○ {esc(q["text"])}</div><div class="who">{esc(q["detail"])}</div></div>'
                       for _, q in mine if not q["closed"])
        rows += "".join(
            f'<div class="q shut"><div class="t">✓ {esc(q["text"])}</div><div class="ev">{esc(q["detail"])}'
            f'{f" <a class=why data-q={i}>为什么 ›</a>" if evidence_note(idea, q["text"]) else ""}</div></div>'
            for i, q in mine if q["closed"])
        title = f'{name} · {names.get(name, "")}'.rstrip(" ·") if name else "这个想法"
        cols += f'<div class="blk"><h3>{esc(title)}</h3><div class="cnt">关掉 {shut} / {len(mine)}</div>{rows}</div>'
    after = f'<p class="next"><span class="label">接下来</span>{esc(idea.get("next"))}</p>' if idea.get("next") else ""
    return f'<p class="say">{say}</p>{agent}{hill}<div class="cols">{cols}</div>{after}'


def drill(idea: dict | None, index: int) -> str:
    """One level down: the note filed under ## 证据 for a closed question."""
    found = questions(idea) if idea else []
    if not 0 <= index < len(found):
        return ""
    q = found[index]
    note = evidence_note(idea, q["text"])
    crumb = f'<div class="crumb"><a data-back>{esc(idea.get("short") or idea.get("idea"))}</a> › {esc(q["slice"])} › {esc(q["text"])}</div>'
    return f'{crumb}<h2>{esc(q["text"])}</h2><p class="src">{esc(q["detail"])}</p>{markdown(note)}'


def markdown(text: str) -> str:
    """Just enough Markdown for an evidence note: paragraphs, bold, images, lists, tables."""
    out, table = [], []
    def flush():
        if table:
            cells = [[c.strip() for c in row.strip("|").split("|")] for row in table if not re.fullmatch(r"\|[\s|:-]+\|", row)]
            out.append("<table>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in cells) + "</table>")
            table.clear()
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("|"):
            table.append(line)
            continue
        flush()
        image = re.fullmatch(r"!\[([^\]]*)\]\(\.\./evidence/([^)]+)\)", line.strip())
        if image:  # images in a row sit side by side, so before and after can be compared
            fig = f'<figure><img src="/evidence/{esc(image.group(2))}"><figcaption>{esc(image.group(1))}</figcaption></figure>'
            if out and out[-1].startswith('<div class="pair">'):
                out[-1] = out[-1][:-6] + fig + "</div>"
            else:
                out.append(f'<div class="pair">{fig}</div>')
        elif line.startswith("- "):
            out.append(f"<p class=li>{inline(line[2:])}</p>")
        elif line.strip():
            out.append(f"<p>{inline(line)}</p>")
    flush()
    return '<div class="note">' + "".join(out) + "</div>"


def inline(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def minutes_ago(idea: dict) -> str:
    minutes = int((time.time() - Path(idea["file"]).stat().st_mtime) // 60)
    return "刚刚" if minutes < 1 else f"{minutes} 分钟前"


def page(root: Path) -> str:
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>走到哪了</title><style>
body{{margin:0;background:#f4f1ea;color:#1b1b1a;font:15px/1.7 -apple-system,"PingFang SC",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:36px 36px 70px}} p{{margin:0}}
.which{{color:#8b867c;font:12px "SF Mono",Menlo,monospace;margin-bottom:18px}}
.state{{font-size:18px;font-weight:600}} .state .quiet{{font-weight:400}}
.alert{{color:#b5541a}} .quiet{{color:#8b867c;font-size:13px}} .state+.quiet{{margin-top:2px}}
.now{{font-size:22px;line-height:1.4;margin:32px 0 36px}}
.label{{color:#8b867c;font-size:13px;margin-right:12px}} .quiet+.list,.state+.list{{margin-top:32px}}
ul{{list-style:none;margin:10px 0 32px;padding:0}} li{{margin:6px 0;color:#8b867c}}
li.here{{color:#1b1b1a}} .mark{{display:inline-block;width:1.6em}} li.done .mark{{color:#4a8f5b}}
.say{{font-size:22px;line-height:1.6;max-width:880px;margin:0 0 8px}} .say .g{{color:#8b867c}}
.say mark{{background:#f6e27a;padding:0 .15em;border-radius:3px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.agent{{font-size:13px;color:#555}} .agent.alert{{color:#b5541a}}
.hill{{width:100%;display:block;margin:18px 0 6px}} .hill text{{font:12px -apple-system,"PingFang SC",sans-serif;fill:#1b1b1a}} .hill .axis{{fill:#8b867c;font-size:11px}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:26px;margin-top:6px}}
.blk h3{{font-size:15px;margin:0}} .cnt{{font:12px "SF Mono",Menlo,monospace;color:#8b867c;margin-bottom:8px}}
.q{{padding:9px 0 11px;border-top:1px solid #d8d2c5}} .q.open .t{{color:#b5541a;font-weight:600}} .q.shut .t{{color:#555}}
.who,.ev{{color:#8b867c;font-size:13px;margin:2px 0 0 1.2em}} .who{{color:#b5541a;opacity:.85}}
.why{{color:#b5541a;cursor:pointer;font:12px "SF Mono",Menlo,monospace;white-space:nowrap}} .why:hover{{text-decoration:underline}}
.next{{margin-top:30px;color:#555}}
pre{{font:14px/1.5 Menlo,"PingFang SC",monospace;white-space:pre;overflow-x:auto;margin:24px 0 16px}}
.term{{border-bottom:1.5px dashed #d06a12;cursor:zoom-in}} .term:hover{{background:#d06a1222}}
.oq{{font-size:16px;margin:26px 0 10px}}
.trace{{border-collapse:collapse;width:100%;font-size:13px}} .trace th{{text-align:left;color:#8b867c;font-weight:500;padding:4px 10px 6px 0}}
.trace td{{border-top:1px solid #d8d2c5;padding:7px 10px 7px 0;vertical-align:top}} .trace .dec{{color:#8b867c;font-size:12px}}
.trace .none{{color:#b3ab9c}} .trace tr.gap td:last-child .none{{color:#b5541a;font-weight:600}}
.gaps{{margin-top:10px;font-size:13px;color:#555}} .gaps summary{{cursor:pointer;color:#b5541a}} .opts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}}
.opt{{background:#fffdf8;border:1px solid #d8d2c5;border-radius:10px;padding:12px}} .opt.rec{{border:2px solid #d06a12}}
.oh{{font-weight:600}} .oh em{{font-style:normal;color:#d06a12;font-size:12px;margin-left:6px}} .looks{{font-size:13px;color:#555;margin:2px 0 10px}}
.kind{{font-size:11.5px;color:#8b867c;margin-top:6px}} .nopic{{height:120px;display:flex;align-items:center;justify-content:center;background:#efebe2;color:#8b867c;border-radius:6px;font-size:13px}}
.frame{{position:relative}} .frame .cover{{position:absolute;inset:0;cursor:zoom-in}}
.frame{{height:400px;overflow:hidden;border:1px solid #d8d2c5;border-radius:6px;background:#fff}}
.opt iframe{{width:900px;height:900px;border:0;transform-origin:0 0;background:#fff}}
#lb iframe{{position:absolute;border:0;border-radius:8px;background:#fff;display:none}}
.fig{{position:relative;line-height:0}} .fig img{{width:100%;border:1px solid #d8d2c5;border-radius:6px;cursor:zoom-in}}
.box{{position:absolute;border:3px solid #d06a12;border-radius:3px;display:none;pointer-events:none}}
#tip{{position:fixed;z-index:30;display:none;width:440px;background:#fffdf8;border:1px solid #d8d2c5;border-radius:10px;box-shadow:0 18px 40px -12px #0005;padding:10px;pointer-events:none}}
#tip p{{font-size:13px;color:#555;margin-top:8px;line-height:1.5}}
#lb{{position:fixed;inset:0;z-index:40;display:none;cursor:zoom-out}} #lb .bg{{position:absolute;inset:0;background:#1b1b1a}}
#lb .fig{{position:absolute}} #lb .fig img{{width:100%;height:100%;border:0;cursor:zoom-out}} #lb p{{position:absolute;left:0;right:0;bottom:18px;text-align:center;color:#f4f1ea;font-size:14px}}
#sheet{{position:fixed;top:0;right:0;bottom:0;width:min(760px,94vw);background:#fbf9f4;box-shadow:-20px 0 60px #0002;transform:translateX(102%);overflow:auto;padding:28px 34px 60px;box-sizing:border-box}}
#scrim{{position:fixed;inset:0;background:#1b1b1a33;display:none}} .crumb{{font:12px "SF Mono",Menlo,monospace;color:#8b867c;margin-bottom:12px}}
.crumb a{{cursor:pointer}} .crumb a:hover{{color:#1b1b1a}} #sheet h2{{font-size:20px;margin:0 0 4px}} .src{{color:#8b867c;margin-bottom:18px}}
.note p{{margin:0 0 10px}} .note .li{{padding-left:1em;text-indent:-1em}} .note .li::before{{content:"· "}}
.pair{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:6px 0 16px}} .note figure{{margin:0}}
.note img{{width:100%;height:320px;object-fit:cover;object-position:left top;border:1px solid #d8d2c5}} .note figcaption{{color:#8b867c;font-size:12px}}
.note table{{border-collapse:collapse;margin:4px 0 16px;font-size:14px}} .note td{{border-top:1px solid #d8d2c5;padding:5px 14px 5px 0}}
@media (prefers-reduced-motion:reduce){{#sheet{{transition:none}}}}
.proj{{margin-top:56px;padding-top:26px;border-top:1px solid #d8d2c5}} .what{{max-width:820px;margin-bottom:22px}}
ul.pl{{margin:0}} ul.pl li{{color:#1b1b1a;margin:0;padding:7px 0;border-top:1px solid #e3ddd0;font-size:14px;line-height:1.5}}
ul.pl .sub{{color:#8b867c;font-size:12px}} ul.pl li.none{{color:#b3ab9c}} .blk details summary{{cursor:pointer;color:#8b867c;font-size:13px;padding:6px 0}}
.proj pre{{font-size:13px;margin:8px 0 0}} pre.out{{background:#fffdf8;border:1px solid #d8d2c5;border-radius:6px;padding:10px;margin:0;font-size:12.5px}}
.scr .fig img{{max-height:340px;object-fit:cover;object-position:left top}}
</style></head><body><main id="m">{body(root)}</main><div id="scrim"></div><div id="sheet"></div>
<div id="tip"></div><div id="lb"><div class="bg"></div><div class="fig"><img alt=""><i class="box"></i></div><iframe sandbox></iframe><p></p></div><script>
function fit(root){{root.querySelectorAll('.frame').forEach(f=>{{const k=f.clientWidth/900;f.querySelector('iframe').style.transform=`scale(${{k}})`;f.style.height=Math.round(900*k*.6)+'px'}})}}
addEventListener('resize',()=>fit(document));
function place(root){{fit(root);root.querySelectorAll('.fig[data-box]').forEach(f=>{{const b=f.dataset.box.split(',').map(Number),im=f.querySelector('img'),bx=f.querySelector('.box');
if(b.length<4||!bx)return;const go=()=>{{const W=im.naturalWidth,H=im.naturalHeight;if(!W)return;Object.assign(bx.style,{{display:'block',
left:b[0]/W*100+'%',top:b[1]/H*100+'%',width:(b[2]-b[0])/W*100+'%',height:(b[3]-b[1])/H*100+'%'}})}};im.complete?go():im.addEventListener('load',go)}})}}
let last='';setInterval(async()=>{{try{{const r=await fetch('/body');const t=await r.text();if(t===last)return;last=t;
const m=document.getElementById('m');m.innerHTML=t;place(m)}}catch(e){{}}}},{POLL_MS});place(document);
const tip=document.getElementById('tip'),lb=document.getElementById('lb'),lf=lb.querySelector('.fig'),lbg=lb.querySelector('.bg');let tw=null,from=null;
function pic(src,box){{return `<div class="fig" data-box="${{box}}"><img src="${{src}}" alt=""><i class="box"></i></div>`}}
document.addEventListener('mouseover',e=>{{const t=e.target.closest('.term');if(!t)return;tip.innerHTML=pic(t.dataset.src,t.dataset.box)+`<p>${{t.dataset.what}}</p>`;place(tip);tip.style.display='block'}});
document.addEventListener('mouseout',e=>{{if(e.target.closest('.term'))tip.style.display='none'}});
document.addEventListener('mousemove',e=>{{if(tip.style.display!=='block')return;let x=e.clientX+18,y=e.clientY+18;
if(x+460>innerWidth)x=e.clientX-470;if(y+tip.offsetHeight>innerHeight)y=Math.max(8,innerHeight-tip.offsetHeight-8);tip.style.left=x+'px';tip.style.top=y+'px'}});
function tween(a,b,ms,done){{clearInterval(tw);const t0=performance.now();const step=()=>{{const p=Math.min(1,(performance.now()-t0)/ms),k=1-Math.pow(1-p,3),r={{}};
for(const q in b)r[q]=a[q]+(b[q]-a[q])*k;Object.assign(lf.style,{{left:r.x+'px',top:r.y+'px',width:r.w+'px',height:r.h+'px'}});lbg.style.opacity=r.o;
if(p>=1){{clearInterval(tw);done&&done()}}}};step();tw=setInterval(step,16)}}
function enlarge(src,box,what,rect){{tip.style.display='none';const im=lf.querySelector('img');lf.dataset.box=box||'';lb.querySelector('p').textContent=what||'';lb.style.display='block';
const go=()=>{{const W=im.naturalWidth,H=im.naturalHeight,s=Math.min(innerWidth*.92/W,innerHeight*.84/H,1.6);from={{x:rect.left,y:rect.top,w:rect.width,h:rect.height,o:0}};
place(lb);tween(from,{{x:(innerWidth-W*s)/2,y:(innerHeight-H*s)/2-16,w:W*s,h:H*s,o:.85}},260)}};im.onload=go;im.src=src;if(im.complete&&im.naturalWidth)go()}}
function shrink(){{if(lb.style.display!=='block')return;const fi=lb.querySelector('iframe');if(fi.style.display==='block'){{fi.style.display='none';fi.src='about:blank';lf.style.display='';lb.style.display='none';return}}const r=lf.getBoundingClientRect();tween({{x:r.left,y:r.top,w:r.width,h:r.height,o:.85}},from,200,()=>lb.style.display='none')}}
document.addEventListener('click',e=>{{if(e.target.closest('#lb')){{shrink();return}}const t=e.target.closest('.term');
if(t){{enlarge(t.dataset.src,t.dataset.box,t.dataset.what,t.getBoundingClientRect());return}}
const f=e.target.closest('main .fig');if(f){{const o=f.closest('.opt');enlarge(f.querySelector('img').src,f.dataset.box,o?o.querySelector('.oh').textContent:'',f.getBoundingClientRect());return}}
const fr=e.target.closest('main .frame');if(fr){{const fi=lb.querySelector('iframe'),o=fr.closest('.opt'),W=Math.min(innerWidth*.9,1100),H=innerHeight*.84;
lf.style.display='none';fi.style.display='block';fi.src=fr.dataset.src;lb.querySelector('p').textContent=o?o.querySelector('.oh').textContent:'';lb.style.display='block';
Object.assign(fi.style,{{left:(innerWidth-W)/2+'px',top:(innerHeight-H)/2-16+'px',width:W+'px',height:H+'px'}});lbg.style.opacity=.85}}}},true);
const sheet=document.getElementById('sheet'),scrim=document.getElementById('scrim');
function slide(from,to,done){{const t0=performance.now(),id=setInterval(()=>{{const k=Math.min(1,(performance.now()-t0)/380),e=1-Math.pow(1-k,3);
sheet.style.transform=`translateX(${{from+(to-from)*e}}%)`;if(k>=1){{clearInterval(id);done&&done()}}}},16)}}
document.addEventListener('click',async ev=>{{const w=ev.target.closest('[data-q]');
if(w){{const r=await fetch('/drill?i='+w.dataset.q);sheet.innerHTML=await r.text();sheet.scrollTop=0;scrim.style.display='block';slide(102,0);return}}
if(ev.target.closest('[data-back]')||ev.target===scrim){{scrim.style.display='none';slide(0,102)}}}});
addEventListener('keydown',e=>{{if(e.key==='Escape'){{shrink();scrim.style.display='none';slide(0,102)}}}});
</script></body></html>"""


# ---------- serving and opening ----------

def state_file(root: Path) -> Path:
    key = hashlib.sha1(str(root).encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"yishuship-page-{key}.json"


def serve(root: Path) -> None:
    last = [time.time()]   # any request; keeps the server alive
    polled = [0.0]         # the last time an open page asked for an update

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            last[0] = time.time()
            if self.path == "/body":
                polled[0] = time.time()
            kind = "text/html; charset=utf-8"
            if self.path == "/ping":
                out = json.dumps({"root": str(root), "page_idle": time.time() - polled[0]}).encode()
            elif self.path.startswith("/drill?i="):
                out = drill(current(str(root)), int(self.path.split("=", 1)[1] or -1)).encode()
            elif self.path.startswith(("/evidence/", "/screens/")):
                name = self.path.split("/")[1]
                folder = (root / ".ship" / name).resolve()
                wanted = (folder / urllib.parse.unquote(self.path[len(name) + 2:])).resolve()
                if not (wanted.is_relative_to(folder) and wanted.is_file()):
                    self.send_error(404)
                    return
                out, kind = wanted.read_bytes(), mimetypes.guess_type(wanted.name)[0] or "application/octet-stream"
            else:
                out = (body(root) if self.path == "/body" else page(root)).encode()
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *_):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state = state_file(root)
    state.write_text(json.dumps({"port": server.server_address[1], "pid": os.getpid()}))

    def watch():
        while time.time() - last[0] < IDLE_EXIT:
            time.sleep(5)
        server.shutdown()
    threading.Thread(target=watch, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # so the finally below still runs
    try:
        server.serve_forever()
    finally:
        state.unlink(missing_ok=True)


def running(root: Path) -> tuple[int, float] | None:
    """Port of a live server for ROOT and seconds since a page last asked it, if any."""
    try:
        port = json.loads(state_file(root).read_text())["port"]
        reply = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=1).read())
        return port, reply["page_idle"]
    except (OSError, ValueError, KeyError):
        return None


def open_page(directory: str) -> int:
    root = project_root(directory)
    if root is None or (current(str(root)) is None and not project_file(root).exists()) or os.environ.get("YISHUSHIP_NO_PAGE"):
        return 0
    live = running(root)
    if live is None:
        subprocess.Popen([sys.executable, __file__, "--serve", str(root)], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            time.sleep(0.1)
            if (live := running(root)) is not None:
                break
        else:
            print("the page server did not start", file=sys.stderr)
            return 1
    port, page_idle = live
    url = f"http://127.0.0.1:{port}/"
    if page_idle < CLOSED_AFTER:  # an open page asks every POLL_MS
        print(f"already open: {url}")
        return 0
    if os.environ.get("CMUX_WORKSPACE_ID") and subprocess.run(["which", "cmux"], capture_output=True).returncode == 0:
        opened = subprocess.run(["cmux", "browser", "open-split", url], capture_output=True, text=True).stdout
        surface = re.search(r"surface=(\S+)", opened)
        print(f"opened beside the terminal: {url}")
        if surface:
            print(f"close with: cmux close-surface --surface {surface.group(1)}")
    else:
        subprocess.run(["open", url])
        print(f"opened in the browser: {url}")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--serve"] and len(argv) == 2:
        serve(Path(argv[1]))
    elif argv[:1] == ["--html"] and len(argv) == 2:
        root = project_root(argv[1])
        print(page(root) if root else "no project here")
    elif len(argv) == 1 and not argv[0].startswith("-"):
        return open_page(argv[0])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
