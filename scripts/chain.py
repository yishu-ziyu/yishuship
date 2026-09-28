"""Draw a project's chain (需求 → 意图 → 设计 → 任务 → 问题) from its .ship files as one expandable page.

  chain.py DIR    print the page for the project at DIR

Draft for 003-T6: not yet part of page.py; chain_serve.py serves it and writes confirmations back.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if __name__ == "__main__" else None
SHIP = ROOT / ".ship" if ROOT else None
SERVED = False
esc = html.escape


def table(text):
    rows = [l for l in text.splitlines() if l.startswith("|") and not re.fullmatch(r"\|[\s|:-]+\|", l.strip())]
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    return [dict(zip(head, [c.strip() for c in r.strip("|").split("|")])) for r in rows[1:]]


def inline(t, base):
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


def md(text, base):
    """Just enough Markdown: headings, lists, checkboxes, tables, code, images."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append(f"<pre>{esc(chr(10).join(lines[i + 1:j]))}</pre>")
            i = j + 1
            continue
        if l.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            rows = table("\n".join(lines[i:j]))
            if rows:
                head = "".join(f"<th>{esc(k)}</th>" for k in rows[0])
                body = "".join("<tr>" + "".join(f"<td>{inline(v, base)}</td>" for v in r.values()) + "</tr>" for r in rows)
                out.append(f"<table><tr>{head}</tr>{body}</table>")
            i = j
            continue
        img = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", l.strip())
        if img:
            src = (base / img.group(2)).resolve()
            url = "/f/" + src.relative_to(SHIP.resolve()).as_posix() if SERVED else src.as_uri()
            out.append(f'<figure><img src="{esc(url)}"><figcaption>{esc(img.group(1))}</figcaption></figure>')
        elif m := re.match(r"#{1,4} (.+)", l):
            out.append(f"<h4>{inline(m.group(1), base)}</h4>")
        elif m := re.match(r"- \[([ xX])\] (.+)", l):
            done = m.group(1) != " "
            out.append(f'<div class="ck{" done" if done else ""}"><span>{"✓" if done else "○"}</span>{inline(m.group(2), base)}</div>')
        elif l.startswith("- "):
            out.append(f'<div class="li">{inline(l[2:], base)}</div>')
        elif l.strip():
            out.append(f"<p>{inline(l, base)}</p>")
        i += 1
    return "".join(out)


def sections(text, pattern):
    return list(re.finditer(pattern + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S))


def field(body, name):
    m = re.search(rf"^{name}：(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def build(root, served=False):
    global ROOT, SHIP, SERVED, nodes, edges
    ROOT, SHIP, SERVED = Path(root).resolve(), Path(root).resolve() / '.ship', served
    nodes, edges = {}, []


    def node(nid, col, kind, title, sub, state, body, tone=""):
        nodes[nid] = {"id": nid, "col": col, "kind": kind, "title": title, "sub": sub, "state": state, "body": body, "tone": tone}


    KEYS = ["来源", "日期", "原话", "当时看到的", "我们的理解", "怎样算解决", "去向"]


    def fields(body):
        out, key = {}, None
        for line in body.splitlines():
            m = re.match(r"^(%s)：(.*)$" % "|".join(KEYS), line)
            if m:
                key = m.group(1)
                out[key] = m.group(2)
            elif key:
                out[key] += "\n" + line
        return {k: v.strip() for k, v in out.items()}


    for m in sections((SHIP / "需求.md").read_text(encoding="utf-8"), r"^## (R-\d+) (.+?)$"):
        rid, f = m.group(1), fields(m.group(3))
        kind = f.get("来源", "").split(" · ")[0]
        body = (f'<dl><dt>来源</dt><dd>{esc(f.get("来源", ""))}</dd><dt>日期</dt><dd>{esc(f.get("日期", ""))}</dd>'
                f'<dt>去向</dt><dd>{esc(f.get("去向", ""))}</dd></dl>'
                f'<h4>原话</h4><blockquote>{esc(f.get("原话", ""))}</blockquote>'
                + (f'<h4>当时看到的</h4>{md(f["当时看到的"], SHIP)}' if f.get("当时看到的") else "")
                + f'<h4>我们的理解 · 推断</h4>{md(f.get("我们的理解", ""), SHIP)}'
                + f'<h4>怎样算解决</h4>{md(f.get("怎样算解决", ""), SHIP)}')
        node(rid, 0, "需求", m.group(2), f"{rid} · {kind}", "", body)
        for t in re.findall(r"\b(\d{3})\b", f.get("去向", "")):
            edges.append((rid, t))

    for adr in sorted((SHIP / "决定").glob("ADR-*.md")):
        text = adr.read_text(encoding="utf-8")
        aid = adr.name.split("-")[0] + "-" + adr.name.split("-")[1]
        node(aid, 2, "决定", text.splitlines()[0].split(" ", 2)[-1], f"{aid} · 架构决定", field(text, "状态"), md("\n".join(text.splitlines()[1:]), adr.parent))

    for d in sorted(p for p in SHIP.iterdir() if re.match(r"\d{3}-", p.name)):
        num = d.name[:3]
        it = (d / "意图.md").read_text(encoding="utf-8")
        node(num, 1, "意图", it.splitlines()[0].split("：", 1)[-1], f"意图 {num}", field(it, "状态"), md("\n".join(it.splitlines()[1:]), d))
        ds = (d / "设计.md").read_text(encoding="utf-8")
        for m in sections(ds, r"^## (§\d) (.+?)$"):
            sid = f"{num}-{m.group(1)}"
            ok = re.search(r"你确认了：(.+)", m.group(3))
            ok = ok.group(1).strip() if ok else ""
            confirmed = bool(ok) and "没有" not in ok
            asks = re.findall(r"^要改（(.+?)）：(.+)$", m.group(3), re.M)
            state = f"你确认了 {ok}" if confirmed else (f"你要改：{asks[-1][1]}" if asks else "等你确认")
            node(sid, 2, "设计", m.group(2), f"设计 {m.group(1)}", state, md(m.group(3), d), "" if confirmed else "wait")
            nodes[sid]["asks"] = [f"{a} 你说：{b}" for a, b in asks] if not confirmed else []
            edges.append((num, sid))
            for a in re.findall(r"ADR-\d+", m.group(3)):
                edges.append((sid, a))
        ver = {m.group(1): m.group(2) for m in sections((d / "验证.md").read_text(encoding="utf-8"), r"^## (\d{3}-T\d+)[^\n]*")}
        probs = table((d / "问题.md").read_text(encoding="utf-8"))
        for m in sections((d / "任务.md").read_text(encoding="utf-8"), r"^## (\d{3}-T\d+) (.+?)$"):
            tid, body = m.group(1), m.group(3)
            steps = re.findall(r"^- \[([ xX])\]", body, re.M)
            done = sum(s != " " for s in steps)
            state = field(body, "状态")
            found = [p for p in probs if p["发现于"] == tid]
            html_body = (f'<div class="prog"><i style="width:{100 * done // max(len(steps), 1)}%"></i></div>'
                         f'<p class="meta">{done}/{len(steps)} 步 · 状态：{esc(state)}</p>'
                         f'<dl><dt>来自</dt><dd>{esc(field(body, "来自"))}</dd><dt>依赖</dt><dd>{esc(field(body, "依赖"))}</dd></dl>'
                         f'<h4>步骤</h4>{md(chr(10).join(l for l in body.splitlines() if l.startswith("- [")), d)}'
                         f'<h4>验证</h4>{md(ver[tid], d) if tid in ver else "<p class=none>还没有验证记录</p>"}')
            tone = {"返工": "warn", "在做": "live", "没开始": "idle"}.get(state, "")
            node(tid, 3, "任务", m.group(2), tid, f"{state} · {done}/{len(steps)}", html_body, tone)
            for s in re.findall(r"§\d", field(body, "来自")):
                edges.append((f"{num}-{s}", tid))
            for s in re.findall(r"R-\d+", field(body, "来自")):
                edges.append((s, tid))
            for s in re.findall(r"\d{3}-T\d+", field(body, "依赖")):
                edges.append((s, tid))
        for p in probs:
            pid = p["编号"]
            body = (f'<dl><dt>发现于</dt><dd>{esc(p["发现于"])}</dd><dt>处理</dt><dd>{esc(p["处理"])}</dd></dl>'
                    f'<blockquote>{esc(p["现象"])}</blockquote>')
            node(pid, 4, "问题", p["现象"], f'{pid} · 发现于 {p["发现于"]}', p["处理"], body)
            edges.append((p["发现于"], pid))
            for s in re.findall(r"R-\d+", p["处理"]):
                edges.append((pid, s))

    edges = [(a, z) for a, z in edges if a in nodes and z in nodes]
    COLS = ["需求", "意图", "设计", "任务", "问题"]
    cards = ""
    for i, name in enumerate(COLS):
        items = "".join(
            f'<div class="n {v["tone"]}" id="{esc(k)}"><div class="s">{esc(v["sub"])}</div><div class="t">{esc(v["title"])}</div>'
            + (f'<div class="st">{esc(v["state"])}</div>' if v["state"] else "") + "</div>"
            for k, v in nodes.items() if v["col"] == i)
        cards += f'<div class="c"><div class="h">{name}</div>{items}</div>'
    idea = next((v for v in nodes.values() if v["kind"] == "意图"), {"id": "", "title": ""})
    data = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)

    page = """<!doctype html><html lang="zh"><meta charset="utf-8"><title>链条</title><style>
    :root{--paper:#f5f4ed;--ivory:#faf9f5;--ink:#141413;--warm:#3d3d3a;--stone:#6b6a64;--mute:#9b9a92;--line:#e5e3d8;--brand:#1B365D;--tint:#E4ECF5;--warn:#9a3b1e;
    --serif:Charter,"Songti SC","Noto Serif SC",Georgia,serif;--sans:-apple-system,"PingFang SC",sans-serif}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.6 var(--serif)}
    main{padding:44px 40px 80px;position:relative;transition:margin-right .25s}body.open main{margin-right:520px}
    .eyebrow{font:12px var(--sans);letter-spacing:.14em;color:var(--brand)} h1{font-weight:400;font-size:30px;margin:8px 0 4px}
    .lede{color:var(--stone);margin:0 0 28px}
    .grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:36px;position:relative;z-index:1}
    .h{font:12px var(--sans);letter-spacing:.1em;color:var(--mute);padding-bottom:8px;border-bottom:1px solid var(--line);margin-bottom:12px}
    .n{background:var(--ivory);border:1px solid var(--line);border-radius:6px;padding:9px 11px;margin-bottom:10px;cursor:pointer;transition:opacity .15s,border-color .15s}
    .n:hover{border-color:#c9c3b3}.n .s{font:11.5px var(--sans);color:var(--brand)}
    .n .t{font-size:13.5px;line-height:1.5;margin:2px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .n .st{font:11.5px var(--sans);color:var(--stone)} .n.warn .st,.n.wait .st{color:var(--warn)} .n.live .st{color:var(--brand)}
    .n.sel{border-color:var(--brand);background:#fff;box-shadow:0 0 0 1px var(--brand)} .n.on{border-color:var(--brand);background:#fff}
    .dim .n:not(.on):not(.sel){opacity:.3}
    svg{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}path{fill:none;stroke:var(--brand);stroke-width:1.4}
    aside{position:fixed;top:0;right:0;bottom:0;width:520px;background:#fffdf8;border-left:1px solid var(--line);transform:translateX(100%);transition:transform .25s;overflow:auto;padding:30px 34px 60px}
    body.open aside{transform:none}
    .x{position:absolute;top:18px;right:22px;font:13px var(--sans);color:var(--mute);cursor:pointer}
    .kind{font:12px var(--sans);letter-spacing:.12em;color:var(--brand)} aside h2{font-weight:400;font-size:22px;line-height:1.4;margin:6px 0 14px}
    aside h4{font:600 12px var(--sans);letter-spacing:.08em;color:var(--stone);margin:22px 0 8px}
    aside p{margin:0 0 10px} aside .none{color:var(--mute)} aside code{font:12.5px Menlo,monospace;background:#f1efe6;padding:1px 4px;border-radius:3px}
    aside pre{font:12px/1.5 Menlo,"PingFang SC",monospace;background:#f6f4ec;padding:12px;border-radius:6px;overflow:auto;white-space:pre}
    aside table{border-collapse:collapse;font-size:12.5px;width:100%}aside td,aside th{border-top:1px solid var(--line);padding:5px 8px 5px 0;text-align:left;vertical-align:top}
    aside blockquote{margin:12px 0;padding:10px 14px;border-left:3px solid var(--brand);background:var(--tint);font-size:15px}
    dl{display:grid;grid-template-columns:52px 1fr;gap:4px 12px;margin:0 0 8px;font-size:13.5px}dt{font:12px/1.9 var(--sans);color:var(--mute)}dd{margin:0}
    .ck{display:flex;gap:10px;padding:5px 0;border-top:1px solid var(--line);font-size:13.5px}.ck span{width:1em;color:var(--mute)}.ck.done{color:var(--stone)}.ck.done span{color:#4a8f5b}
    .li{padding-left:1em;text-indent:-1em}.li:before{content:"· "}
    .prog{height:4px;background:var(--line);border-radius:2px;overflow:hidden}.prog i{display:block;height:100%;background:var(--brand)}
    .meta{font:12px var(--sans);color:var(--stone);margin-top:6px}
    figure{margin:8px 0 14px}figure img{width:100%;border:1px solid var(--line);border-radius:4px}figcaption{font:12px var(--sans);color:var(--mute)}
    .links{display:flex;flex-direction:column;gap:6px;margin-bottom:6px}.lk{font-size:13px;padding:6px 10px;border:1px solid var(--line);border-radius:5px;cursor:pointer;background:var(--ivory)}
    .lk:hover{border-color:var(--brand)}.lk b{font:500 11.5px var(--sans);color:var(--brand);margin-right:6px}
    .ask{margin:18px 0 6px;padding:14px 16px;border:1px solid var(--brand);border-radius:8px;background:#fff}.ask p{margin:0 0 10px;font-size:14px}.ask .b{display:flex;gap:10px}.ask button{font:14px var(--sans);padding:8px 16px;border-radius:999px;border:1px solid var(--brand);background:#fff;color:var(--brand);cursor:pointer}.ask button.y{background:var(--brand);color:#fff}.ask textarea{width:100%;margin-top:10px;font:13px var(--sans);border:1px solid var(--line);border-radius:6px;padding:8px;height:56px}.ask .msg{font:12.5px var(--sans);color:var(--warn);margin-top:6px}</style><body><main id="m"><div class="eyebrow">YISHUSHIP · 链条</div><h1>__TITLE__</h1>
    <p class="lede">点任何一张卡，右边展开它的全部内容。图上亮起的是它的完整来历，和它直接引出的下一步；右边的上下游可以继续点，顺着链一路走下去。</p>
    <svg id="g"></svg><div class="grid">__CARDS__</div></main>
    <aside id="a"><span class="x" id="x">关闭 ✕</span><div id="d"></div></aside><script>
    const D=__DATA__,m=document.getElementById('m'),g=document.getElementById('g'),d=document.getElementById('d');let cur=null;
    const up=id=>D.edges.filter(e=>e[1]===id).map(e=>e[0]),down=id=>D.edges.filter(e=>e[0]===id).map(e=>e[1]);
    function reach(id,dir){const seen=new Set([id]),q=[id];while(q.length){const x=q.shift();for(const n of dir?down(x):up(x)){if(!seen.has(n)){seen.add(n);if(!n.startsWith('R-'))q.push(n)}}}return seen}
    const lit=id=>new Set([...reach(id,0),...down(id)]);
    function lines(){g.innerHTML='';if(!cur)return;const b=m.getBoundingClientRect(),s=lit(cur);
    for(const[a,z]of D.edges){if(!s.has(a)||!s.has(z))continue;const A=document.getElementById(a),Z=document.getElementById(z),r1=A.getBoundingClientRect(),r2=Z.getBoundingClientRect();
    let x1=r1.right-b.left,x2=r2.left-b.left;if(r2.left<r1.left){x1=r1.left-b.left;x2=r2.right-b.left}if(Math.abs(r2.left-r1.left)<5){x1=r1.left-b.left;x2=r2.left-b.left}
    const y1=r1.top+r1.height/2-b.top,y2=r2.top+r2.height/2-b.top,dx=Math.abs(r2.left-r1.left)<5?-36:(x2-x1)/2;
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',`M${x1},${y1} C${x1+dx},${y1} ${x2-dx},${y2} ${x2},${y2}`);g.appendChild(p)}}
    const link=id=>{const n=D.nodes[id];return `<div class="lk" data-go="${id}"><b>${n.kind} ${id}</b>${n.title.length>46?n.title.slice(0,46)+'…':n.title}</div>`};
    function open(id){cur=id;const n=D.nodes[id],s=lit(id);
    document.querySelectorAll('.n').forEach(x=>{x.classList.toggle('on',s.has(x.id));x.classList.toggle('sel',x.id===id)});m.classList.add('dim');
    const u=up(id),w=down(id);
    const ask=(n.kind==='设计'&&!n.state.startsWith('你确认了'))?`<div class="ask">${(n.asks||[]).length?`<p><b>你要改的：</b>${n.asks.join('；')}</p><p>我改完后会再请你确认。</p>`:'<p>这份设计在等你确认。确认之后，按它拆出来的任务才能开工。</p>'}<div class="b"><button class="y" data-ok="${id}">可以，照这个做</button><button data-fix="${id}">要改</button></div><textarea id="note" placeholder="要改的话，写一句哪里不对，再点「要改」"></textarea><div class="msg" id="msg"></div></div>`:'';
    d.innerHTML=`<div class="kind">${n.kind} · ${id}</div><h2>${n.title}</h2>${ask}${n.state&&n.kind!=='任务'?`<p class="meta">${n.state}</p>`:''}${n.body}
    <h4>上游 · 它从哪来</h4>${u.length?`<div class="links">${u.map(link).join('')}</div>`:'<p class="none">没有上游</p>'}
    <h4>下游 · 它引出了什么</h4>${w.length?`<div class="links">${w.map(link).join('')}</div>`:'<p class="none">还没有下游</p>'}`;
    document.body.classList.add('open');setTimeout(()=>{lines();document.getElementById('a').scrollTop=0},260)}
    function close(){cur=null;document.body.classList.remove('open');m.classList.remove('dim');document.querySelectorAll('.n').forEach(x=>x.classList.remove('on','sel'));setTimeout(lines,260)}
    async function send(id,ok){const note=(document.getElementById('note')||{}).value||'';const msg=document.getElementById('msg');if(!ok&&!note.trim()){msg.textContent='先写一句哪里要改';return}if(location.protocol==='file:'){msg.textContent='这是离线预览，按钮只在本机服务打开的页面里有效';return}const r=await fetch('/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,ok,note})});if(r.ok)location.href='/?pick='+encodeURIComponent(id);else msg.textContent='没写进去：'+await r.text()}
document.addEventListener('click',e=>{const y=e.target.closest('[data-ok]');if(y){send(y.dataset.ok,true);return}const f=e.target.closest('[data-fix]');if(f){send(f.dataset.fix,false);return}const go=e.target.closest('[data-go]');if(go){open(go.dataset.go);return}const n=e.target.closest('.n');if(n){open(n.id);return}
    if(e.target.id==='x'||!e.target.closest('aside'))close()});addEventListener('keydown',e=>{if(e.key==='Escape')close()});addEventListener('resize',lines);
    const pick=new URLSearchParams(location.search).get('pick');if(pick)open(pick);
    </script></body></html>"""
    out = page.replace("__TITLE__", esc(f'{idea["id"]} {idea["title"]}')).replace("__CARDS__", cards).replace("__DATA__", data)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1]))
