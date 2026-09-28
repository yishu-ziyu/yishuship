#!/usr/bin/env python3
"""A page beside the terminal: a note from the agent whose first sentence says whether the user needs to act;
a second view shows the project as a whole from .ship/PROJECT.md.

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
from ideas import (STALE_MINUTES, _section, _serves, current, doing, load, project_file, project_root,  # noqa: E402
                   quiet_for, slice_things, trace, visuals)

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


def slice_key(text: str) -> str:
    """`第一块 点引用跳原文` → `第一块`."""
    found = re.match(r"[\s\"']*(第.+?块)", text or "")
    return found.group(1) if found else ""


def finished(idea: dict) -> dict | None:
    """The last slice ticked off in ## 进度, with its note under ## 证据 when there is one."""
    text = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    progress = _section(text, "进度")
    ticked = re.findall(r"^- \[[xX]\] +(.+)$", progress, flags=re.M)
    if not ticked:
        return None
    line = ticked[-1]
    key = slice_key(line)
    later = re.search(r"^- \[ \] +(第.+?块)", progress, flags=re.M)
    out = {"key": key or line.split(" · ")[0], "committed": bool(re.search(r"\b[0-9a-f]{7,40}\b", line)),
           "next": later.group(1) if later else "", "note": evidence_for(idea, key)}
    return out


def evidence_for(idea: dict, key: str) -> str | None:
    """The note under ## 证据 headed `### <key> …`."""
    text = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    for m in re.finditer(r"^### +(.+?)\n(.*?)(?=^### |\Z)", _section(text, "证据"), flags=re.M | re.S):
        if key and m.group(1).strip().startswith(key):
            return m.group(2)
    return None


def listed_pictures(idea: dict, heading: str) -> list[tuple[str, str]]:
    """`### <heading>` under ## 看得见: `- <what it shows> · ../evidence/<file>`, as (caption, file)."""
    text = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    found = re.search(rf"^### +{heading}\n(.*?)(?=^### |\Z)", _section(text, "看得见"), flags=re.M | re.S)
    return re.findall(r"^- +(.+?)\s*·\s*\.\./evidence/(\S+?)\s*$", found.group(1) if found else "", flags=re.M)


def latest_picture(idea: dict, root: Path) -> tuple[str, str] | None:
    """The newest screenshot of the running product this idea's file points at, for the working state:
    from ## 证据 and `### 现在`, never a question's options or mocks."""
    text = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    found = re.findall(r"!\[(.*?)\]\(\.\./evidence/([^)]+?\.(?:png|jpe?g|gif|webp))\)", _section(text, "证据"))
    found += [p for p in listed_pictures(idea, "现在") if re.search(r"\.(png|jpe?g|gif|webp)$", p[1])]
    files = [(root / ".ship" / "evidence" / path, alt, path) for alt, path in found]
    files = [f for f in files if f[0].is_file()]
    if not files:
        return None
    _, alt, path = max(files, key=lambda f: f[0].stat().st_mtime)
    return alt, path


def parse_choices(block: str) -> tuple[str, list[dict]]:
    """The choices layout of asking.md read back: what comes before ①, then each question with its
    options (letter, label, recommended, the lines under it)."""
    lead, groups, opt = [], [], None
    for line in block.splitlines():
        text = line.strip().strip("│").strip()
        q = re.match(r"^([①-⑳])\s*(.+)$", text)
        o = re.match(r"^[├└]─+\s*([A-Z])\s+(.+?)\s*(◀\s*推荐)?$", text)
        if q:
            groups.append({"q": q.group(2).strip(), "opts": []})
            opt = None
        elif o and groups:
            opt = {"letter": o.group(1), "label": o.group(2).strip(), "rec": bool(o.group(3)), "looks": ""}
            groups[-1]["opts"].append(opt)
        elif text and opt is not None and not text.startswith("回复示例"):
            cjk = opt["looks"][-1:] > "\u2e7f" and text[:1] > "\u2e7f"  # Chinese lines join without a space
            opt["looks"] = (opt["looks"] + ("" if cjk else " ") + text).strip()
        elif text and not groups and not text.startswith("[yishuship]") and text not in ("▼", "│"):
            lead.append(re.sub(r"^▼\s*", "", text))
    return " → ".join(lead), [g for g in groups if g["opts"]]


def proof_parts(note: str) -> dict:
    """From a slice's evidence note: the pictures, which behaviors it proves and how, what it did not verify."""
    body, _, missed = note.partition("#### 没验证到的")
    missed = re.split(r"^#{3,4} ", missed, maxsplit=1, flags=re.M)[0]
    return {"pictures": re.findall(r"^!\[(.*)\]\(\.\./evidence/([^)]+)\)\s*$", body, flags=re.M),
            "proves": _serves(body),
            "how": {f"行为{n}": rest.strip() for n, rest, _ in re.findall(r"^- *行为(\d+)\s*[·:：✓]\s*(.+)$(\n\s*细节[：:].*)?", body, flags=re.M)},
            "detail": {f"行为{n}": d.strip() for n, d in re.findall(r"^- *行为(\d+)\s*[·:：✓].*\n\s*细节[：:]\s*(.+)$", body, flags=re.M)},
            "missed": [re.sub(r"^- +", "", line).strip() for line in missed.splitlines() if line.strip()]}


def feedback(idea: dict) -> list[dict]:
    """## 你的反馈, written by the page: notes pinned on a picture, and the answer to 满意吗."""
    text = Path(idea["file"]).read_text(encoding="utf-8") if idea.get("file") else ""
    out = []
    for done, rest in re.findall(r"^- \[([ xX])\] +(.+)$", _section(text, "你的反馈"), flags=re.M):
        parts = [p.strip() for p in rest.split(" · ")]
        ref = parts.pop() if len(parts) > 2 and "../evidence/" in parts[-1] else ""
        path, _, frag = ref.partition("#")
        box = re.fullmatch(r"box=(\d+),(\d+),(\d+),(\d+)", frag)
        answer = re.match(r"你的回答[：:](满意|不行)", parts[1]) if len(parts) > 1 else None
        out.append({"done": done != " ", "text": " · ".join(parts[1:]), "answer": answer.group(1) if answer else "",
                    "src": "/evidence/" + path.split("../evidence/", 1)[1] if path else "",
                    "box": [int(n) for n in box.groups()] if box else None})
    return out


def add_feedback(file: Path, line: str) -> None:
    """Append one line under ## 你的反馈, creating it above ## 进度 when missing."""
    text = file.read_text(encoding="utf-8")
    if not re.search(r"^## 你的反馈\n", text, flags=re.M):
        anchor = re.search(r"^## (进度|决定|证据)\n", text, flags=re.M)
        at = anchor.start() if anchor else len(text)
        text = text[:at] + "## 你的反馈\n\n" + text[at:]
    m = re.search(r"^## 你的反馈\n(.*?)(?=^#{1,2} |\Z)", text, flags=re.M | re.S)
    lines = [l for l in m.group(1).splitlines() if l.strip()] + [line]
    file.write_text(text[:m.start(1)] + "\n".join(lines) + "\n\n" + text[m.end(1):], encoding="utf-8")


def answer(file: Path, said: str, note: str) -> None:
    """The user answered 满意吗 on the page: note it, add a row to ## 决定, stop waiting.
    The agent acts on it at the next /yishuship and ticks the line off."""
    today = time.strftime("%Y-%m-%d")
    add_feedback(file, f"- [ ] {today} · 你的回答：{said}" + (f" · {note}" if note else ""))
    text = re.sub(r"^waiting:.*$", "waiting:", file.read_text(encoding="utf-8"), count=1, flags=re.M)
    why = "在页面上点了满意" if said == "满意" else "在页面上点了不行" + (f"：{note}" if note else "")
    m = re.search(r"^## 决定\n(?:.*\n)*?(\|.*\|\n)(?!\|)", text, flags=re.M)
    row = f"| {today} | {said} | {why} |\n"
    text = text[:m.end()] + row + text[m.end():] if m else text
    file.write_text(text, encoding="utf-8")


# ---------- drawing it ----------
# A note from the agent in the first person. Its first sentence always answers
# "do I need to do anything"; the project as a whole is a second view.

GLOSS = {
    "块": "最小的、能单独给人用的一段。后面的都不做，它也成立。",
    "证据": "在真实运行的 App 里截的两张图，并排放。只说“测试通过”不算做完。",
    "行为": "用户做什么 → 看到什么。每条都要能在真实产品里点出来验证。",
}
RECOMMEND = '<span class="tag tag-accent">我推荐</span>'
FOOT = "虚线下划线的词，把鼠标放上去看解释。"
COUNT = "零一两三四五六七八九十"
NTH = "零一二三四五六七八九十"


def esc(text: str) -> str:
    return html.escape(text or "")


def gl(word: str, meaning: str) -> str:
    """A word with a dotted underline; hovering it puts its meaning in the line at the bottom."""
    return f'<span class="gl" tabindex="0" data-gl="{esc(meaning)}">{esc(word)}</span>'


def cn(n: int) -> str:
    return COUNT[n] if 0 < n <= 10 else str(n)


def copy_button(text: str, primary: bool = True) -> str:
    return (f'<button type="button" class="btn {"btn-primary" if primary else "btn-secondary"}" '
            f'data-copy="{esc(text)}">复制 {esc(text)}</button>')


def body(root: Path) -> str:
    idea = current(str(root))
    name = root.name + (f' · {"bug · " if idea.get("kind") == "bug" else ""}{idea.get("short") or idea.get("idea")}'
                        if idea else "")
    top = (f'<header class="top"><span class="which">{esc(name)}</span><div class="seg">'
           '<label class="seg-opt"><input type="radio" name="view" value="now" checked>现在</label>'
           '<label class="seg-opt"><input type="radio" name="view" value="project">项目</label></div></header>')
    return (f'{top}<div class="view v-now">{main_body(idea, root)}</div>'
            f'<div class="view v-proj">{project_view(root, idea)}</div>')


def main_body(idea: dict | None, root: Path) -> str:
    """Exactly one state: showing and asking 满意吗, a one-way-door choice, working, maybe stuck, idle."""
    if idea is None:
        return '<p class="open">这个项目现在没有进行中的想法。</p>'
    question = waiting_block(idea)
    said = next((f for f in reversed(feedback(idea)) if f["answer"] and not f["done"]), None)
    if said and not question:
        ok = said["answer"] == "满意"
        return (f'<h1 class="{"" if ok else "alert"}">记下了：{"满意" if ok else "先停下，重新聊"}。</h1>'
                f'<p class="lead">已经写进进度文件。我不会自己醒来：下次你在终端里打 /yishuship，我先读到这句'
                f'{"和你在图上指的地方" if any(f["box"] and not f["done"] for f in feedback(idea)) else ""}，'
                f'{"然后提交这一块，接着往下做" if ok else "然后停下来跟你重新聊"}。</p>'
                f'<div class="btns">{copy_button("/yishuship")}</div>')
    if question and idea.get("waiting", "").startswith("满意吗"):
        return show_view(idea, question)
    if question:
        return ask_view(idea, question)
    step, thing, place, _ = doing(idea)
    what = thing or step
    age = quiet_for(idea) if idea.get("now") else ""
    if age:
        file, home = Path(idea["file"]).resolve(), root.resolve()
        file = file.relative_to(home).as_posix() if file.is_relative_to(home) else str(file)
        out = (f'<h1 class="alert">我已经 {esc(age.removesuffix("前"))}没有动静了。</h1>'
               f'<p class="lead">{f"上次我在<b>{esc(what)}</b>。" if what else ""}可能卡住了，也可能会话已经关了。</p>'
               f'<div class="end"><p class="say">在终端里打这个，我会从停下的地方接着做：</p>'
               f'<div class="btns">{copy_button("/yishuship")}</div></div>'
               f'<p class="small">进度都记在 {esc(file)} 里，不会丢。</p>')
    elif idea.get("now"):
        things = slice_things(idea)
        count = (f'这一块有 {len(things)} 件事，做完了 {sum(d for d, _ in things)} 件。' if things else "")
        rows = "".join(
            f'<li class="{"done" if d else ("here" if n == place else "todo")}">'
            f'<span class="mark">{"✓" if d else ("◐" if n == place else "○")}</span>{esc(text)}</li>'
            for n, (d, text) in enumerate(things, 1))
        out = ('<h1>你可以去忙别的。</h1>'
               f'<p class="lead">我正在<b>{esc(what)}</b>。{count}做完后我会停下来，'
               f'把{gl("改之前和改之后", GLOSS["证据"])}的截图放在这里给你看。</p>'
               + (f'<ul class="things">{rows}</ul>' if rows else "")
               + (f'<div class="blk"><p class="small">最近一张截图</p>{pictures_html([latest])}</div>'
                  if (latest := latest_picture(idea, root)) else "")
               + f'<p class="small">上次更新：{esc(minutes_ago(idea))}。如果 {STALE_MINUTES} 分钟没有新消息，这里会提醒你。</p>')
    else:
        last = finished(idea)
        was = ""
        if last:
            was = f'{esc(last["key"])}已经做完{"、也提交了" if last["committed"] else ""}。'
        after = f'下一步是<b>{esc(idea["next"])}</b>。' if idea.get("next") else "下一步还没定。"
        out = ('<h1>我停在这里，等你叫我。</h1>'
               f'<p class="lead">{was}{after}</p>'
               f'<div class="end"><p class="say">要我接着做，在终端里打：</p><div class="btns">{copy_button("/yishuship")}</div></div>')
    return out


def ask_view(idea: dict, question: str) -> str:
    """A choice only the user can make: while shaping, the mocks first (你是说这样吗), then each
    question with its options side by side as pictures; the reply is built as you pick."""
    seen = visuals(idea)
    groups = [g for g in seen["options"] if g["opts"]]
    mocks = listed_pictures(idea, "你是说这样吗")
    key = slice_key(idea.get("slice", ""))
    if idea.get("status") == "shaping" or (finished(idea) is None and (mocks or "做不做" in question)):
        where = "这个想法我先照我的理解画了一下。" if mocks else "这个想法我先理了一下。"
        top = (f'<p class="open">{where}</p>{pictures_html(mocks)}<p class="say">你是说这样吗？下面是只有你能定的事。</p>'
               if mocks else f'<p class="open">{where}下面的事只有你能定。</p>')
    else:
        where = f'我做到{gl(key, GLOSS["块"])}，停下来了。' if key else "我停下来了。"
        top = f'<p class="open">{where}下面{cn(len(groups)) if groups else "的"}事只有你能定。</p>'
    lead = ""
    if not groups:  # no option pictures were written: read the options back from the block itself
        lead, groups = parse_choices(question)
        for g in groups:
            for o in g["opts"]:
                o.update(src="", kind="没有图", box=None)
        lead = f'<p class="lead">{esc(lead)}</p>' if lead else ""
    if not groups:  # not in the choices layout: the block as it was shown in the terminal
        return (f'{top}<pre class="block">{with_terms(question, seen["terms"])}</pre>'
                '<p class="say">在终端里回复你的选择，我接着做。</p>')
    top += lead
    marked = any(o["rec"] for g in groups for o in g["opts"])
    out = top.replace("只有你能定。</p>", f'只有你能定{"，我在推荐的那个上做了标记" if marked else ""}。</p>', 1)
    code = []
    for n, group in enumerate(groups, 1):
        pick = next((o["letter"] for o in group["opts"] if o["rec"]), group["opts"][0]["letter"])
        code.append(f"{n}{pick}")
        cards = ""
        for o in group["opts"]:
            if o["src"].endswith(".html"):
                media = (f'<div class="frame" data-src="{esc(o["src"])}"><iframe src="{esc(o["src"])}" sandbox loading="lazy"'
                         ' tabindex="-1"></iframe><i class="cover"></i></div>')
            else:
                media = figure(o)
            chosen = o["letter"] == pick
            cap = o["kind"] + (" · 点图看大图" if media else "")
            pic = f'<div class="pic halftone">{media}<span class="cap">{esc(cap)}</span></div>' if media else ""
            cards += (f'<div class="card opt{" sel" if chosen else ""}" role="radio" tabindex="0" aria-checked="{str(chosen).lower()}"'
                      f' data-pick="{esc(o["letter"])}">{pic}'
                      f'<div class="ob"><div class="row"><span class="mk">{"●" if chosen else "○"} {esc(o["letter"])}</span>'
                      f'{RECOMMEND if o["rec"] else ""}</div>'
                      f'<div class="ot">{with_terms(o["label"], seen["terms"])}</div>'
                      f'<div class="oc">{with_terms(o["looks"], seen["terms"])}</div></div></div>')
        title = re.sub(r"^[①-⑳]\s*", "", group["q"])
        out += (f'<section class="q" data-n="{n}" data-key="{esc(group["q"])}" data-default="{esc(pick)}" role="radiogroup">'
                f'<p class="nth">第{NTH[n] if n <= 10 else n}件</p><h2>{with_terms(title, seen["terms"])}</h2>'
                f'<div class="opts{" many" if len(group["opts"]) >= 3 else ""}">{cards}</div></section>')
    reply = " ".join(code)
    return (out + f'<div class="end"><p class="reply">你的回复是 <b data-code>{esc(reply)}</b>。复制后贴回终端，我接着做。</p>'
            f'<div class="btns"><button type="button" class="btn btn-primary" data-copy="/yishuship {esc(reply)}" data-reply>'
            f'复制 /yishuship {esc(reply)}</button></div></div>')


def pictures_html(items: list[tuple[str, str]], stack: bool = False) -> str:
    """Pictures side by side, each with its caption; an .html mock is shown live, scaled down."""
    out = ""
    for alt, path in items[:2]:
        head, _, rest = alt.partition(" · ")
        src = "/evidence/" + path.split("#")[0]
        media = (f'<div class="frame shot" data-src="{esc(src)}"><iframe src="{esc(src)}" sandbox loading="lazy" tabindex="-1">'
                 '</iframe><i class="cover"></i></div>' if src.endswith(".html")
                 else f'<div class="fig shot" data-box=""><img src="{esc(src)}" alt="{esc(alt)}"></div>')
        out += f'<figure>{media}<figcaption><b>{esc(head)}</b>{" · " + esc(rest) if rest else ""}</figcaption></figure>'
    return f'<div class="pair{" stack" if stack else ""}">{out}</div>' if out else ""


def show_view(idea: dict, question: str) -> str:
    """The usual stop: the product as it is now, and one question, 满意吗.

    At the end of a slice: before and after from its note under ## 证据, each behavior with its
    proof, what was not verified. Stopped early: 原本想 / 现在 / 难在哪 from the block, with the
    pictures under `### 现在` in ## 看得见."""
    said = dict(re.findall(r"^\s*(现在|原本想|难在哪|满意|不行)\s*(?:→\s*)?(.+?)\s*$", question, flags=re.M))
    early = "原本想" in said or "难在哪" in said
    key = slice_key(idea.get("slice", ""))
    done = finished(idea)
    note = done["note"] if done and not early else evidence_for(idea, key)
    parts = proof_parts(note or "")
    pictures = listed_pictures(idea, "现在") if early else []
    pics = compare(idea, pictures or parts["pictures"])
    if early:
        opening = f'<p class="open">{esc(key or "这一块")}比预想的难。我先停下来，给你看现在的样子。</p>'
        line = lambda name: f'<div class="blk"><h2>{name}</h2><p class="say">{esc(said[name])}</p></div>' if name in said else ""
        body_html = line("原本想") + pics + line("现在") + line("难在哪")
    else:
        name = done["key"] if done else (key or "这一块")
        opening = (f'<p class="open">{esc(name)}做完了。我在真实的 App 里点了一遍，下面是'
                   f'{gl("改之前和改之后", GLOSS["证据"])}。</p>')
        names = {b["id"]: b["text"] for b in trace(idea)["behaviors"]}
        how = {b: f'<span class="ev">{esc(text)}</span>' for b, text in parts["how"].items()}
        for b, text in parts["detail"].items():  # how it was measured stays one click away
            how[b] = how.get(b, "") + f'<details class="detail"><summary>细节</summary>{esc(text)}</details>'
        proven = "".join(f'<li><span class="ok">✓</span><span>{esc(names.get(b, b))}{how.get(b, "")}</span></li>'
                         for b in parts["proves"])
        missed = "".join(f"<p>{esc(line)}</p>" for line in parts["missed"]) or '<p class="grey">证据里没写这一节。</p>'
        body_html = (pics + (f'<div class="blk"><h2>说好的，都做到了</h2><ul class="proven">{proven}</ul></div>' if proven else "")
                     + f'<div class="blk"><h2>我没验证到的</h2><div class="missed">{missed}</div></div>')
    tidy = lambda t: t.strip().rstrip("，,；;。. ")
    yes = tidy(said.get("满意") or "") or ("提交这一块，接着做" + (done["next"] if done and done["next"] else "下一块"))
    no = tidy(said.get("不行") or "") or "我停在这里，我们重新聊"
    return (opening + body_html
            + f'<div class="end" id="answer"><p class="reply">满意吗？点 <b>满意</b>，{esc(yes)}；点 <b>不行</b>，{esc(no)}。</p>'
            '<div class="btns"><button type="button" class="btn btn-primary" data-answer="满意">满意，接着做</button>'
            '<button type="button" class="btn btn-secondary" data-answer="不行">不行，重新聊</button></div>'
            '<p class="small">点了就写进进度文件；也可以照旧在终端里回「满意」或「不行」。</p></div>')


def compare(idea: dict, items: list[tuple[str, str]]) -> str:
    """Before and after on one picture, split by a handle you drag; one picture alone when there is one.
    Above it, the tool to point at a spot and say what is wrong; below, the spots already pointed at."""
    items = [(alt, path.split("#")[0]) for alt, path in items if not path.split("#")[0].endswith(".html")]
    if not items:
        return ""
    (a_alt, a_path), (b_alt, b_path) = items[0], items[1] if len(items) > 1 else (None, None)
    after, after_alt = ("/evidence/" + (b_path or a_path)), (b_alt or a_alt)
    head = lambda alt: alt.partition(" · ")[0] or alt
    rest = lambda alt: alt.partition(" · ")[2]
    notes = [f for f in feedback(idea) if f["box"] and f["src"] == after and not f["done"]]
    boxes = "".join(f'<i class="pin" data-box="{",".join(map(str, f["box"]))}"><span>{n}</span></i>' for n, f in enumerate(notes, 1))
    layers = (f'<img class="under" src="{esc(after)}" alt="{esc(after_alt)}">'
              + (f'<div class="clip"><img src="/evidence/{esc(a_path)}" alt="{esc(a_alt)}"></div>'
                 f'<span class="tag-l">{esc(head(a_alt))}</span><span class="tag-r">{esc(head(b_alt))}</span>'
                 '<div class="handle"><button type="button" class="knob" aria-label="左右拖动，对比改之前和改之后">⇔</button></div>'
                 if b_path else ""))
    caps = (f'<span><b>{esc(head(a_alt))}</b>{" · " + esc(rest(a_alt)) if rest(a_alt) else ""}</span>'
            + (f'<span><b>{esc(head(b_alt))}</b>{" · " + esc(rest(b_alt)) if rest(b_alt) else ""}</span>' if b_path else ""))
    listed = "".join(f'<li data-n="{n}"><span class="pn">{n}</span>{esc(f["text"])}</li>' for n, f in enumerate(notes, 1))
    return (f'<div class="cmp"><div class="tools"><span class="small" data-hint>'
            f'{"左右拖动圆钮对比；" if b_path else ""}哪里不对，就在图上框出来。</span>'
            '<button type="button" class="btn btn-secondary" data-point>在图上指出来 <kbd>P</kbd></button></div>'
            f'<div class="stage{" two" if b_path else ""}" data-src="{esc(after)}">{layers}{boxes}</div>'
            f'<div class="caps{" two" if b_path else ""}">{caps}</div>'
            + (f'<ul class="notes">{listed}</ul>' if listed else "") + '</div>')


def project_view(root: Path, idea: dict | None) -> str:
    """3g: the project as a whole, from .ship/PROJECT.md and the idea files."""
    file = project_file(root)
    if not file.exists():
        return '<p class="open">这个项目还没有 .ship/PROJECT.md。</p>'
    text = file.read_text(encoding="utf-8")
    items = lambda name: [m.group(1).strip() for m in re.finditer(r"^- (.+)$", _section(text, name), flags=re.M)]
    plain = lambda name: re.sub(r"<!--.*?-->", "", _section(text, name), flags=re.S).strip()
    what = re.sub(r"\s*[（(]出自[^）)]*[）)]\s*$", "", plain("这是什么"))
    out = (f'<p class="open proj">{esc(what if what.startswith(root.name) else f"{root.name} 是{what}")}</p>'
           if what else "")

    can = []  # every behavior users can do: proven, or built with nothing proving it
    for each in load(root):
        if each.get("status") == "dropped":
            continue
        linked = trace(each)
        unlinked = not any(e["proves"] for e in linked["evidence"]) and any(s["done"] for s in linked["slices"])
        for b in linked["behaviors"]:
            if b["proven_by"]:
                can.append((b["text"], True))
            elif b["built"] or (unlinked and b["decided"]):
                can.append((b["text"], False))
    rows = "".join(f'<li><span>{esc(t)}</span><span class="{"yes" if ok else "no"}">{"有证据" if ok else "做了，没证据"}</span></li>'
                   for t, ok in can)
    out += (f'<div class="blk"><p class="say">现在用户能做 <b>{len(can)} 件事</b>，其中 {sum(ok for _, ok in can)} 件我拿到了'
            f'{gl("证据", GLOSS["证据"])}：</p><ul class="rows">{rows}</ul></div>' if can
            else '<div class="blk"><p class="say">用户现在还不能用上任何做出来的东西。</p></div>')

    ideas = ""
    for row in items("想法"):
        parts = [p for p in re.sub(r"\[[^\]]+\]\([^)]+\)", "", row).split(" · ") if p.strip()]
        state = parts.pop() if len(parts) > 1 else ""
        cls = "tag-accent" if state == "在做" else "tag-accent-2" if state == "等你决定" else "tag-neutral"
        ideas += f'<li><span class="tag {cls}">{esc(state)}</span><span>{esc(" · ".join(parts))}</span></li>'
    if ideas:
        out += f'<div class="blk"><p class="say">手上有 <b>{len(items("想法"))} 个想法</b>：</p><ul class="ideas">{ideas}</ul></div>'

    owed = ""
    for row in items("待办和技术债"):
        main, _, where = row.partition(" · 来自")
        where = re.sub(r"^「(.*)」$", r"做「\1」时看到", where.strip())
        owed += f'<li>{inline(main)}{f"<span class=grey> · {esc(where)}</span>" if where else ""}</li>'
    if owed:
        out += f'<div class="blk"><p class="say">还欠着 <b>{len(items("待办和技术债"))} 件</b>，不在这次范围里：</p><ul class="owed">{owed}</ul></div>'

    out += trace_view(idea) if idea else ""

    built = plain("怎么搭的")
    fence = re.search(r"```[^\n]*\n(.*?)```", built, flags=re.S)
    if fence or built:
        drawing = f'<pre class="built">{esc(fence.group(1).rstrip())}</pre>' if fence else f'<p class="say">{inline(built)}</p>'
        out += f'<div class="blk"><p class="say">它是这样搭起来的：</p>{drawing}</div>'

    screens = ""
    for row in items("界面现在长什么样"):
        found = re.search(r"screens/[^\s·)]+", row)
        ref = found.group(0) if found else ""
        label = re.sub(r"\s*·?\s*" + re.escape(ref) + r"\s*·?\s*", " · ", row).strip(" ·") if ref else row
        label = re.sub(r"\d{4}-0?(\d{1,2})-0?(\d{1,2})", r"\1 月 \2 日", label)
        target = root / ".ship" / ref
        if ref.endswith(".txt") and target.is_file():
            media = f"<pre class=out>{esc(target.read_text(encoding='utf-8', errors='replace').rstrip())}</pre>"
        elif ref and target.is_file():
            media = f'<div class="fig" data-box=""><img src="/{esc(ref)}" alt="{esc(label)}"></div>'
        else:
            media = '<span class="cap">没有截图</span>'
        screens += f'<figure><div class="shot halftone">{media}</div><figcaption>{esc(label)}</figcaption></figure>'
    if screens:
        out += f'<div class="blk"><p class="say">界面现在长这样：</p><div class="pair">{screens}</div></div>'
    return out


def trace_view(idea: dict) -> str:
    """Each behavior with what serves and proves it, folded; a break is counted on the fold."""
    t = trace(idea)
    if not t["behaviors"] or not any(b["designs"] or b["slices"] or b["proven_by"] for b in t["behaviors"]):
        return ""
    cell = lambda xs: "".join(f"<div>{esc(x)}</div>" for x in xs) or '<div class="grey">—</div>'
    rows = ""
    for b in t["behaviors"]:
        if b["proven_by"]:
            proof = cell(b["proven_by"])
        elif b["built"]:
            proof = '<div class="no">做了，没证据</div>'
        else:
            proof = '<div class="grey">还没做</div>'
        rows += (f'<tr><td>{esc(b["text"])}<div class="dec">{"定了" if b["decided"] else "待定"}</div></td>'
                 f'<td>{cell(b["designs"])}</td><td class="nw">{cell([slice_key(x) or x for x in b["slices"]])}</td><td>{proof}</td></tr>')
    gaps = "".join(f"<li>{esc(g)}</li>" for g in t["gaps"])
    broken = f'<span class="no small">{len(t["gaps"])} 处断开</span>' if t["gaps"] else ""
    return (f'<div class="blk trace"><button type="button" class="fold" data-fold aria-expanded="false">'
            f'<span class="tri">▸</span><span>每件事是怎么一路落到证据上的</span>{broken}</button>'
            f'<div class="folded" hidden><table class="table"><thead><tr><th>用户能看到的{gl("行为", GLOSS["行为"])}</th>'
            f'<th>设计</th><th>哪一块</th><th>证据</th></tr></thead><tbody>{rows}</tbody></table>'
            + (f'<ul class="gaps">{gaps}</ul>' if gaps else "") + "</div></div>")


def figure(item: dict, cls: str = "fig") -> str:
    """A picture with the thing it points at boxed; the box is placed once the image loads."""
    box = ",".join(map(str, item["box"])) if item.get("box") else ""
    return (f'<div class="{cls}" data-box="{box}"><img src="{esc(item["src"])}" alt=""><i class="box"></i></div>'
            if item.get("src") else "")


def with_terms(block: str, terms: list[dict]) -> str:
    """The text as written, with every named thing that has a picture underlined: hover to see it."""
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


def inline(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def minutes_ago(idea: dict) -> str:
    minutes = int((time.time() - Path(idea["file"]).stat().st_mtime) // 60)
    return "刚刚" if minutes < 1 else f"{minutes} 分钟前"


def page(root: Path) -> str:
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>走到哪了</title><script>if(location.hash==='#project')document.documentElement.classList.add('proj')</script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap"><style>
:root{{--bg:#f3f2f2;--surface:#eae9e9;--ink:#201e1d;--a:#0088b0;--a1:#e9f8ff;--a6:#1186ac;--a7:#006786;--m:#d6006c;--m7:#aa0b56;
--n2:#eae7e7;--n3:#d7d3d3;--n5:#9b9797;--n6:#7d7979;--n7:#605d5d;--line:color-mix(in srgb,#201e1d 16%,transparent);
--md:0 3px 10px rgba(45,43,43,.16);--lg:0 12px 32px rgba(45,43,43,.22)}}
html,body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 "Source Serif 4",system-ui,sans-serif}}
main{{max-width:720px;box-sizing:border-box;padding:32px 44px 0}} p,h1,h2,ul,figure{{margin:0}} ul{{list-style:none;padding:0}}
h1,h2{{font-weight:600}} b{{font-weight:600}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:16px}} .which{{font-size:15px;color:var(--n6)}}
.seg{{display:inline-flex;flex-shrink:0;overflow:hidden;border:1px solid var(--line);border-radius:2px}}
.seg-opt{{display:inline-flex;align-items:center;padding:7px 12px;font-size:13px;cursor:pointer;white-space:nowrap}}
.seg-opt input{{position:absolute;opacity:0;pointer-events:none}} .seg-opt+.seg-opt{{border-left:1px solid var(--line)}}
.seg-opt:has(input:checked){{background:var(--a);color:var(--bg)}} .seg-opt:not(:has(input:checked)):hover{{background:var(--a1)}}
.seg-opt:has(input:focus-visible){{outline:2px solid var(--a);outline-offset:2px}}
.view{{padding:48px 0 40px;display:flex;flex-direction:column;gap:40px}} .v-proj,html.proj .v-now{{display:none}} html.proj .v-proj{{display:flex}}
.open{{font-size:30px;line-height:1.45;font-style:italic;text-wrap:pretty}} .open.proj{{font-size:28px}}
h1{{font-size:46px;line-height:1.15}} h1.alert{{color:var(--m7)}} .lead{{font-size:24px;line-height:1.55;text-wrap:pretty}}
.say{{font-size:20px;line-height:1.55;text-wrap:pretty}} .reply{{font-size:22px;line-height:1.5}} .reply b{{color:var(--a7)}}
.small{{font-size:15px;color:var(--n6)}} .grey{{color:var(--n6)}} .no{{color:var(--m7)}} .yes{{color:var(--a7)}}
h2{{font-size:22px;line-height:1.3}} .blk{{display:flex;flex-direction:column;gap:10px}} .end{{display:flex;flex-direction:column;gap:14px}}
.btns{{display:flex;gap:12px;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;cursor:pointer;font:600 14px/1.2 "Source Serif 4",system-ui,sans-serif;color:var(--ink);
background:transparent;border:1px solid transparent;padding:10px 18px;border-radius:2px;white-space:nowrap;flex-shrink:0}}
.btn-primary{{background:var(--a);color:var(--bg)}} .btn-primary:hover{{background:var(--a6)}} .btn-primary:active{{background:var(--a7)}}
.btn-secondary{{border-color:var(--line)}} .btn-secondary:hover{{background:var(--a1)}}
.tag{{display:inline-flex;align-items:center;font-size:11px;letter-spacing:.02em;padding:3px 10px;border-radius:1.5px;white-space:nowrap}}
.tag-accent{{background:var(--a1);color:#004961}} .tag-accent-2{{background:#fff1f4;color:#790e3d}} .tag-neutral{{background:#f8f4f4;color:#444141}}
.halftone{{position:relative;filter:grayscale(.35) contrast(1.15);overflow:hidden}}
.halftone::after{{content:"";position:absolute;inset:0;pointer-events:none;background-image:radial-gradient(circle,rgba(0,0,0,.22) 30%,transparent 32%);background-size:3px 3px;mix-blend-mode:multiply}}
.gl{{border-bottom:1px dotted currentColor;cursor:help}} .open .gl{{border-bottom-width:1.5px}}
.term{{border-bottom:1px dotted currentColor;cursor:zoom-in}} .term:hover{{background:var(--a1)}}
a{{color:var(--a7);cursor:pointer;text-decoration:none}} a:hover{{background:var(--a1)}}
:focus-visible{{outline:2px solid var(--a);outline-offset:2px}}
.q{{display:flex;flex-direction:column;gap:6px}} .nth{{font-size:15px;color:var(--m)}} .q h2{{font-size:26px;margin-bottom:12px}}
.opts{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.card{{display:flex;flex-direction:column;border-radius:2px;background:var(--surface);padding:0;overflow:hidden;cursor:pointer}}
.card{{position:relative}} .card:hover{{box-shadow:var(--md)}} .card.sel::after{{content:"";position:absolute;inset:0;border:2px solid var(--a);z-index:2;pointer-events:none}} .card:focus-visible{{outline-offset:2px}}
.pic{{height:240px;background:var(--n2)}} .opts.many{{grid-template-columns:1fr}} .opts.many .pic,.opts.many .frame{{height:300px}} .pic .fig img{{border:0}}
.cap{{position:absolute;left:10px;bottom:8px;font-size:12px;color:var(--n7);z-index:1;pointer-events:none}}
.pic .cap{{background:color-mix(in srgb,var(--n2) 85%,transparent);padding:0 4px}}
.ob{{display:flex;flex-direction:column;gap:6px;padding:16px}} .row{{display:flex;justify-content:space-between;align-items:center;gap:8px}}
.mk{{font-size:14px;color:var(--n5)}} .sel .mk{{color:var(--a7)}} .ot{{font-size:19px;font-weight:600;line-height:1.35}} .oc{{font-size:15px;line-height:1.55;color:var(--n7)}}
.frame{{position:relative;height:240px;overflow:hidden;background:#fff}} .frame .cover{{position:absolute;inset:0;cursor:zoom-in}}
.frame iframe{{width:900px;height:900px;border:0;transform-origin:0 0;background:#fff;pointer-events:none}}
.fig{{position:relative;line-height:0}} .fig img{{width:100%;cursor:zoom-in}}
.box{{position:absolute;border:3px solid var(--m);border-radius:2px;display:none;pointer-events:none}}
pre{{font:16px/1.6 "Source Serif 4",system-ui,sans-serif;white-space:pre;overflow-x:auto;margin:0}} pre.built{{padding-left:20px}}
pre.block{{font:14px/1.5 ui-monospace,"SF Mono",Menlo,"PingFang SC",monospace}} pre.out{{font-size:12px;line-height:1.4;padding:10px;background:#fff}}
.rows li,.owed li,.ideas li,.things li{{font-size:17px;line-height:1.5}} .rows,.owed,.ideas{{padding-left:20px;display:flex;flex-direction:column;gap:6px}}
.ev{{display:block;font-size:15px;color:var(--n6)}} .detail{{font-size:14px;color:var(--n6)}} .detail summary{{cursor:pointer;color:var(--a7);width:fit-content}}
.rows li{{display:flex;justify-content:space-between;gap:16px}} .rows li>span:last-child{{white-space:nowrap}}
.ideas li{{display:flex;gap:12px;align-items:center}} .owed .grey{{font-size:15px}}
.things{{display:flex;flex-direction:column;gap:8px}} .things li{{display:flex;gap:14px;color:var(--n5)}} .mark{{width:20px;flex-shrink:0}}
.things li.done .mark{{color:var(--a)}} .things li.here{{color:var(--ink);font-weight:600}}
.pair{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}} .pair figure{{display:flex;flex-direction:column;gap:8px}}
.pair figcaption{{font-size:15px;line-height:1.5}} .pair.stack{{grid-template-columns:1fr}} .pair.stack .shot{{height:auto;max-height:420px}} .shot{{height:220px;overflow:hidden;background:var(--n2);position:relative}} .v-proj .shot{{height:150px}}
.proven{{display:flex;flex-direction:column;gap:12px}} .proven li{{display:flex;gap:14px;font-size:18px;line-height:1.5}} .ok{{color:var(--a)}}
.missed p{{font-size:18px;line-height:1.6}} .missed p.grey{{color:var(--n6)}}
.fold{{align-self:flex-start;display:flex;gap:10px;align-items:baseline;border:0;background:transparent;padding:0;font:inherit;font-size:20px;line-height:1.55;color:var(--ink);cursor:pointer;text-align:left}}
.fold:hover{{color:var(--a7)}} .tri{{color:var(--a);width:14px}} .fold .small{{font-size:15px}}
.table{{width:100%;border-collapse:collapse;font-size:15px}} .table th{{text-align:left;font-size:13px;font-weight:400;color:var(--n6);padding:10px;border-bottom:1px solid var(--line)}}
.table td{{padding:10px;vertical-align:top;border-bottom:1px solid color-mix(in srgb,var(--ink) 8%,transparent)}} .table .dec{{font-size:13px;color:var(--n6)}} .nw{{white-space:nowrap}}
.gaps{{margin-top:12px;font-size:15px;color:var(--n7);display:flex;flex-direction:column;gap:4px}}
#foot{{max-width:720px;box-sizing:border-box;padding:14px 44px 18px;min-height:42px;font-size:14px;line-height:1.5;color:var(--n6)}}
#tip{{position:fixed;z-index:30;display:none;width:440px;background:var(--bg);border-radius:2px;box-shadow:var(--lg);padding:10px;pointer-events:none}}
#tip p{{font-size:14px;color:var(--n7);margin-top:8px;line-height:1.5}}
#lb{{position:fixed;inset:0;z-index:40;display:none;cursor:zoom-out}} #lb .bg{{position:absolute;inset:0;background:var(--ink)}}
#lb .fig{{position:absolute}} #lb .fig img{{width:100%;height:100%;cursor:zoom-out}} #lb p{{position:absolute;left:0;right:0;bottom:18px;text-align:center;color:var(--bg);font-size:15px}}
#lb iframe{{position:absolute;border:0;border-radius:2px;background:#fff;display:none}}
.cmp{{display:flex;flex-direction:column;gap:10px}} .tools{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}}
kbd{{font:12px system-ui;border:1px solid currentColor;border-radius:3px;padding:0 4px;opacity:.7;margin-left:6px}}
[data-point].on{{background:var(--m);color:#fff;border-color:var(--m)}}
.stage{{position:relative;overflow:hidden;background:var(--n2);border-radius:2px;box-shadow:var(--md);user-select:none;touch-action:none;line-height:0}}
.stage img{{display:block;width:100%;pointer-events:none}} .stage .clip{{position:absolute;inset:0;overflow:hidden;clip-path:inset(0 50% 0 0);transition:clip-path .45s cubic-bezier(.2,.8,.2,1)}}
.stage .clip img{{position:absolute;inset:0;height:100%;object-fit:cover;object-position:left top}}
.handle{{position:absolute;top:0;bottom:0;left:50%;width:0;transition:left .45s cubic-bezier(.2,.8,.2,1)}} .handle::before{{content:"";position:absolute;top:0;bottom:0;left:-1px;width:2px;background:#fff;box-shadow:0 0 0 1px rgba(0,0,0,.25)}}
.stage.drag .clip,.stage.drag .handle{{transition:none}}
.knob{{position:absolute;top:50%;left:0;transform:translate(-50%,-50%);width:38px;height:38px;border-radius:50%;border:0;background:#fff;box-shadow:var(--md);font-size:14px;line-height:1;cursor:ew-resize;color:var(--ink)}}
.tag-l,.tag-r{{position:absolute;top:10px;font-size:13px;line-height:1.4;padding:2px 9px;background:rgba(32,30,29,.72);color:#fff;transition:opacity .3s}} .tag-l{{left:10px}} .tag-r{{right:10px}}
.stage.pointing{{cursor:crosshair}} .stage.pointing .handle{{opacity:0;pointer-events:none}}
.pin{{position:absolute;border:2px solid var(--m);background:rgba(214,0,108,.08);border-radius:2px;pointer-events:none;animation:pop .25s cubic-bezier(.2,.8,.2,1)}}
.pin span{{position:absolute;left:-2px;top:-22px;background:var(--m);color:#fff;font-size:12px;line-height:1.5;padding:0 7px}} .pin.hot{{background:rgba(214,0,108,.22)}} .pin.draft{{border-style:dashed;animation:none}}
@keyframes pop{{from{{transform:scale(.96);opacity:0}}to{{transform:none;opacity:1}}}}
.ask{{position:absolute;z-index:5;width:300px;background:var(--bg);box-shadow:var(--lg);padding:12px;border-radius:2px;display:flex;flex-direction:column;gap:8px;line-height:1.5;animation:pop .2s}}
.ask textarea,#answer textarea{{font:inherit;font-size:15px;border:1px solid var(--line);padding:8px;resize:none;height:64px;background:#fff}} .ask .btns{{justify-content:flex-end}} .ask .btn{{padding:6px 12px}}
.caps{{display:grid;grid-template-columns:1fr;gap:16px;font-size:15px;color:var(--n7)}} .caps.two{{grid-template-columns:1fr 1fr}} .caps b{{color:var(--ink)}}
.notes{{display:flex;flex-direction:column;gap:6px}} .notes li{{display:flex;gap:10px;font-size:17px;padding:4px 6px;border-radius:2px}} .notes li:hover{{background:#fff1f4}}
.pn{{background:var(--m);color:#fff;font-size:12px;padding:1px 7px;height:fit-content;margin-top:4px}}
@media (prefers-reduced-motion:reduce){{.stage *,.pin,.ask{{transition:none!important;animation:none!important}}}}
@media (max-width:640px){{.opts{{grid-template-columns:1fr}}}}
@media (max-width:560px){{main{{padding:24px 20px 0}} #foot{{padding:14px 20px 18px}} .opts,.pair{{grid-template-columns:1fr}} .open{{font-size:26px}} h1{{font-size:38px}}}}
</style></head><body><main id="m">{body(root)}</main><footer id="foot">{FOOT}</footer>
<div id="tip"></div><div id="lb"><div class="bg"></div><div class="fig"><img alt=""><i class="box"></i></div><iframe sandbox></iframe><p></p></div><script>
const S=sessionStorage,m=document.getElementById('m'),foot=document.getElementById('foot'),FOOT=foot.textContent;
function fit(root){{root.querySelectorAll('.frame').forEach(f=>{{f.querySelector('iframe').style.transform=`scale(${{f.clientWidth/900}})`}})}}
addEventListener('resize',()=>fit(document));
function zoom(f,b,W,H){{const c=f.parentElement,cw=c.clientWidth,ch=c.clientHeight;if(!cw||!ch)return;
let rw=(b[2]-b[0])*1.8,rh=(b[3]-b[1])*1.8;if(rw/rh<cw/ch)rw=rh*cw/ch;else rh=rw*ch/cw;rw=Math.min(rw,W);rh=Math.min(rh,H);
const k=Math.min(cw/rw,ch/rh),x=Math.max(0,Math.min(W-rw,(b[0]+b[2]-rw)/2)),y=Math.max(0,Math.min(H-rh,(b[1]+b[3]-rh)/2));
Object.assign(f.style,{{position:'absolute',width:W*k+'px',left:-x*k+'px',top:-y*k+'px'}})}}
function place(root){{fit(root);root.querySelectorAll('.fig[data-box]').forEach(f=>{{const b=f.dataset.box.split(',').map(Number),im=f.querySelector('img'),bx=f.querySelector('.box');
if(b.length<4||!bx)return;const go=()=>{{const W=im.naturalWidth,H=im.naturalHeight;if(!W)return;if(f.closest('.pic'))zoom(f,b,W,H);Object.assign(bx.style,{{display:'block',
left:b[0]/W*100+'%',top:b[1]/H*100+'%',width:(b[2]-b[0])/W*100+'%',height:(b[3]-b[1])/H*100+'%'}})}};im.complete?go():im.addEventListener('load',go)}})}}
function picks(){{const code=[];m.querySelectorAll('.q').forEach(q=>{{const l=S.getItem('pick:'+q.dataset.key)||q.dataset.default;
let hit=false;q.querySelectorAll('[data-pick]').forEach(c=>{{const on=c.dataset.pick===l;hit=hit||on;c.classList.toggle('sel',on);c.setAttribute('aria-checked',on);
c.querySelector('.mk').textContent=(on?'● ':'○ ')+c.dataset.pick}});code.push(q.dataset.n+(hit?l:q.dataset.default))}});
if(!code.length)return;const t=code.join(' '),b=m.querySelector('[data-code]'),r=m.querySelector('[data-reply]');if(b)b.textContent=t;
if(r&&!r.dataset.busy){{r.dataset.copy='/yishuship '+t;r.textContent='复制 /yishuship '+t}}}}
function folds(){{m.querySelectorAll('[data-fold]').forEach(f=>{{const open=S.getItem('fold')==='1';f.setAttribute('aria-expanded',open);
f.querySelector('.tri').textContent=open?'▾':'▸';f.nextElementSibling.hidden=!open}})}}
function sync(){{const p=location.hash==='#project';document.documentElement.classList.toggle('proj',p);
m.querySelectorAll('input[name=view]').forEach(i=>i.checked=(i.value==='project')===p);picks();folds();place(m)}}
addEventListener('hashchange',sync);
m.addEventListener('change',e=>{{if(e.target.name!=='view')return;history.replaceState(null,'',e.target.value==='project'?'#project':location.pathname);sync()}});
let last='';async function refresh(){{try{{const r=await fetch('/body');const t=await r.text();if(t===last||m.querySelector('.ask,#answer textarea'))return;last=t;m.innerHTML=t;sync()}}catch(e){{}}}}
setInterval(refresh,{POLL_MS});
let cmp=.5,pointing=false,swept=false;const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
function stage(){{return m.querySelector('.stage')}}
function setCmp(p,anim=true){{const st=stage();if(!st||!st.classList.contains('two'))return;cmp=Math.max(0,Math.min(1,p));st.classList.toggle('drag',!anim);
st.querySelector('.clip').style.clipPath=`inset(0 ${{100-cmp*100}}% 0 0)`;st.querySelector('.handle').style.left=cmp*100+'%';
st.querySelector('.tag-l').style.opacity=cmp<.06?0:1;st.querySelector('.tag-r').style.opacity=cmp>.94?0:1}}
function pins(){{const st=stage();if(!st)return;const im=st.querySelector('img.under');const go=()=>{{const W=im.naturalWidth,H=im.naturalHeight;if(!W)return;
st.querySelectorAll('.pin[data-box]').forEach(p=>{{const b=p.dataset.box.split(',').map(Number);Object.assign(p.style,{{left:b[0]/W*100+'%',top:b[1]/H*100+'%',width:(b[2]-b[0])/W*100+'%',height:(b[3]-b[1])/H*100+'%'}})}})}};
im.complete?go():im.addEventListener('load',go,{{once:true}})}}
function cmpSync(){{const st=stage();if(!st)return;pins();const btn=m.querySelector('[data-point]');if(btn)btn.classList.toggle('on',pointing);st.classList.toggle('pointing',pointing);
if(pointing||m.querySelector('.pin[data-box]'))cmp=0;setCmp(cmp,false);
if(!swept&&!still&&st.classList.contains('two')&&!pointing){{swept=true;[.2,.8,.5].forEach((p,i)=>setTimeout(()=>setCmp(p),450+i*500))}}}}
const _sync=sync;sync=function(){{_sync();cmpSync()}};sync();
function togglePoint(){{if(!stage())return;pointing=!pointing;const h=m.querySelector('[data-hint]');if(h)h.textContent=pointing?'在图上拖一个框，框住不对的地方。按 Esc 退出。':'哪里不对，就在图上框出来。';
if(pointing)cmp=0;cmpSync();if(pointing)setCmp(0)}}
let start=null,draft=null,dragging=false;
const rel=(st,e)=>{{const r=st.getBoundingClientRect();return{{x:(e.clientX-r.left)/r.width,y:(e.clientY-r.top)/r.height}}}};
const put=(el,b)=>Object.assign(el.style,{{left:b[0]*100+'%',top:b[1]*100+'%',width:(b[2]-b[0])*100+'%',height:(b[3]-b[1])*100+'%'}});
m.addEventListener('pointerdown',e=>{{const st=e.target.closest('.stage');if(!st||st.querySelector('.ask'))return;
if(pointing){{start=rel(st,e);draft=document.createElement('i');draft.className='pin draft';st.appendChild(draft);st.setPointerCapture(e.pointerId);e.preventDefault();return}}
if(st.classList.contains('two')){{dragging=true;st.setPointerCapture(e.pointerId);setCmp(rel(st,e).x,false);e.preventDefault()}}}});
m.addEventListener('pointermove',e=>{{const st=e.target.closest('.stage');if(!st)return;if(start&&draft){{const p=rel(st,e);put(draft,[Math.min(start.x,p.x),Math.min(start.y,p.y),Math.max(start.x,p.x),Math.max(start.y,p.y)])}}
else if(dragging)setCmp(rel(st,e).x,false)}});
m.addEventListener('pointerup',e=>{{const st=e.target.closest('.stage');dragging=false;if(st)st.classList.remove('drag');if(!st||!start)return;
const p=rel(st,e),b=[Math.min(start.x,p.x),Math.min(start.y,p.y),Math.max(start.x,p.x),Math.max(start.y,p.y)];start=null;
if((b[2]-b[0])*st.clientWidth<12||(b[3]-b[1])*st.clientHeight<12){{draft.remove();draft=null;return}}askNote(st,b)}});
function askNote(st,b){{const a=document.createElement('div');a.className='ask';a.innerHTML='<b>这里怎么了？</b><textarea placeholder="比如：高亮太多了，只要被引用的那一段"></textarea><div class="btns"><button type="button" class="btn btn-secondary" data-x>取消</button><button type="button" class="btn btn-primary" data-ok>记下 ↵</button></div>';
const r=st.getBoundingClientRect();a.style.left=Math.max(0,Math.min(b[0]*r.width,r.width-310))+'px';a.style.top=Math.min(b[3]*r.height+8,Math.max(0,r.height-160))+'px';st.appendChild(a);
const t=a.querySelector('textarea');t.focus();const close=()=>{{a.remove();if(draft){{draft.remove();draft=null}}}};a.querySelector('[data-x]').onclick=close;
const ok=async()=>{{if(!t.value.trim()){{t.focus();return}}const im=st.querySelector('img.under'),W=im.naturalWidth,H=im.naturalHeight;
await fetch('/feedback',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{src:st.dataset.src,text:t.value,box:[b[0]*W,b[1]*H,b[2]*W,b[3]*H].map(Math.round)}})}});
close();pointing=false;refresh()}};a.querySelector('[data-ok]').onclick=ok;
t.onkeydown=e=>{{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();ok()}}if(e.key==='Escape'){{e.stopPropagation();close()}}}}}}
async function send(said,note){{await fetch('/answer',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{answer:said,note}})}});last='';const t=m.querySelector('#answer textarea');if(t)t.remove();refresh()}}
m.addEventListener('click',e=>{{if(e.target.closest('[data-point]')){{togglePoint();return}}
const a=e.target.closest('[data-answer]');if(!a)return;if(a.dataset.answer==='满意'){{send('满意','');return}}
const box=m.querySelector('#answer');let t=box.querySelector('textarea');if(!t){{t=document.createElement('textarea');t.placeholder='哪里不行？可以不写，你在图上框的地方会一起带上。';box.insertBefore(t,box.querySelector('.small'));t.focus();a.textContent='确认：不行';return}}
send('不行',t.value)}});
m.addEventListener('click',e=>{{const li=e.target.closest('.notes li');if(!li)return}});
m.addEventListener('mouseover',e=>{{const li=e.target.closest('.notes li');m.querySelectorAll('.pin').forEach((p,i)=>p.classList.toggle('hot',!!li&&String(i+1)===li.dataset.n))}});
addEventListener('keydown',e=>{{if(e.target.closest&&e.target.closest('textarea'))return;if((e.key==='p'||e.key==='P')&&m.querySelector('[data-point]'))togglePoint();
if(e.key==='Escape'&&pointing)togglePoint();const k=e.target.closest&&e.target.closest('.knob');if(k&&e.key==='ArrowLeft')setCmp(cmp-.05);if(k&&e.key==='ArrowRight')setCmp(cmp+.05)}});
function pick(c){{const q=c.closest('.q');S.setItem('pick:'+q.dataset.key,c.dataset.pick);picks()}}
document.addEventListener('click',e=>{{const c=e.target.closest('[data-pick]');if(c&&!e.target.closest('.pic .fig,.pic .frame')){{pick(c);return}}
const f=e.target.closest('[data-fold]');if(f){{S.setItem('fold',S.getItem('fold')==='1'?'0':'1');folds();return}}
const b=e.target.closest('[data-copy]');if(b){{navigator.clipboard.writeText(b.dataset.copy).then(()=>{{b.dataset.busy=1;b.textContent='已复制';
setTimeout(()=>{{delete b.dataset.busy;b.textContent='复制 '+b.dataset.copy;picks()}},1600)}})}}}});
m.addEventListener('keydown',e=>{{const c=e.target.closest('[data-pick]');if(c&&(e.key==='Enter'||e.key===' ')){{e.preventDefault();pick(c)}}}});
const gloss=e=>{{const g=e.target.closest&&e.target.closest('.gl');if(g)foot.textContent=g.dataset.gl}};
const plain=e=>{{if(e.target.closest&&e.target.closest('.gl'))foot.textContent=FOOT}};
document.addEventListener('mouseover',gloss);document.addEventListener('focusin',gloss);document.addEventListener('mouseout',plain);document.addEventListener('focusout',plain);
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
const label=el=>{{const o=el.closest('.opt'),f=el.closest('figure');return o?o.querySelector('.ot').textContent:f?f.querySelector('figcaption').textContent:''}};
document.addEventListener('click',e=>{{if(e.target.closest('#lb')){{shrink();return}}const t=e.target.closest('.term');
if(t){{enlarge(t.dataset.src,t.dataset.box,t.dataset.what,t.getBoundingClientRect());return}}
const f=e.target.closest('main .fig');if(f&&!f.closest('.stage')){{enlarge(f.querySelector('img').src,f.dataset.box,label(f),f.getBoundingClientRect());return}}
const fr=e.target.closest('main .frame');if(fr){{const fi=lb.querySelector('iframe'),W=Math.min(innerWidth*.9,1100),H=innerHeight*.84;
lf.style.display='none';fi.style.display='block';fi.src=fr.dataset.src;lb.querySelector('p').textContent=label(fr);lb.style.display='block';
Object.assign(fi.style,{{left:(innerWidth-W)/2+'px',top:(innerHeight-H)/2-16+'px',width:W+'px',height:H+'px'}});lbg.style.opacity=.85}}}},true);
addEventListener('keydown',e=>{{if(e.key==='Escape')shrink()}});
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

        def do_POST(self):
            last[0] = time.time()
            idea = current(str(root))
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except ValueError:
                data = {}
            file = Path(idea["file"]) if idea else None
            if file and self.path == "/feedback" and str(data.get("text", "")).strip() and data.get("src", "").startswith("/evidence/"):
                box = ",".join(str(int(v)) for v in data.get("box", [])[:4])
                note = " ".join(str(data["text"]).split()).replace(" · ", "，")
                add_feedback(file, f"- [ ] {time.strftime('%Y-%m-%d')} · {note} · ../{data['src'].lstrip('/')}#box={box}")
            elif file and self.path == "/answer" and data.get("answer") in ("满意", "不行") and idea.get("waiting", "").startswith("满意吗"):
                answer(file, data["answer"], " ".join(str(data.get("note") or "").split()).replace(" · ", "，"))
            else:
                self.send_error(400)
                return
            self.send_response(204)
            self.end_headers()

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
    if os.environ.get("YISHUSHIP_NO_PAGE"):
        print("no page: turned off (YISHUSHIP_NO_PAGE); show everything in the terminal")
        return 0
    if root is None or (current(str(root)) is None and not project_file(root).exists()):
        print("no page: nothing in progress here; show everything in the terminal")
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
            print("no page: the page server did not start; show everything in the terminal")
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
