// Shared by every version: the data, the address (#/类型/编号), and the detail page.
const ST = {done:"做完",doing:"在做",open:"没开始",wait:"等你确认",parked:"搁置",redo:"返工"};
const esc = t => String(t ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function md(t){ // just enough: code fences, bullets, paragraphs, `code`
  const out=[]; const parts=String(t||"").split(/```[^\n]*\n([\s\S]*?)```/);
  parts.forEach((p,i)=>{ if(i%2){out.push(`<pre>${esc(p)}</pre>`);return}
    p.split(/\n\s*\n/).forEach(b=>{b=b.trim(); if(!b)return; const L=b.split("\n");
      if(L.every(l=>/^\s*[-•✓○] /.test(l)||/^\s*[✓○]/.test(l))) out.push("<ul>"+L.map(l=>`<li>${inl(l.replace(/^\s*- /,""))}</li>`).join("")+"</ul>");
      else out.push(`<p>${L.map(inl).join("<br>")}</p>`)})});
  return `<div class="md">${out.join("")}</div>`}
const inl = s => esc(s).replace(/`([^`]+)`/g,"<code>$1</code>").replace(/\*\*(.+?)\*\*/g,"<b>$1</b>");
const st = i => `<span class="st ${i.status}">${ST[i.status]||i.status}</span>`;
const href = (type,id) => "#/"+encodeURIComponent(type)+(id?"/"+encodeURIComponent(id):"");
let D; const I = id => D.items[id];
const ofType = t => Object.values(D.items).filter(i=>i.type===t);
function route(){ const [,t,id]=location.hash.split("/").map(decodeURIComponent); return {type:t||"", id:id||""}}
function crumb(r, home="首页"){ const a=[`<a href="#/">${home}</a>`];
  if(r.type) a.push(`<i>›</i>`, r.id?`<a href="${href(r.type)}">${esc(r.type)}</a>`:`<span>${esc(r.type)}</span>`);
  if(r.id) a.push(`<i>›</i><span>${esc(I(r.id)?.title?.slice(0,24)||r.id)}</span>`);
  return `<nav class="crumb">${a.join("")}</nav>`}
function relLinks(ids){ return ids.filter(I).map(x=>`<a href="${href(I(x).type,x)}"><b>${esc(I(x).type)}</b>${esc(I(x).title)}</a>`).join("")||`<span class="none">无</span>`}
function detail(id, opts={}){ const i=I(id); if(!i) return "<p>找不到这一条</p>";
  const pics=i.images.length?`<div class="pics">${i.images.map(m=>`<figure><img src="${m.src}" alt="${esc(m.alt)}" loading="lazy"><figcaption>${esc(m.alt)}</figcaption></figure>`).join("")}</div>`:"";
  const prog=i.progress?` · 步骤 ${i.progress[0]}/${i.progress[1]}`:"";
  return `<article class="detail">${opts.noCrumb?"":crumb({type:i.type,id})}
   <h1>${esc(i.title)}</h1><div class="meta">${st(i)}<span>${esc(i.type)} ${esc(i.id)}</span>${i.date?`<span>${esc(i.date)}</span>`:""}${i.source?`<span>来源：${esc(i.source)}</span>`:""}<span>${prog}</span></div>
   ${pics}${i.fields.map(([k,v])=>`<section class="field"><h3>${esc(k)}</h3>${md(v)}</section>`).join("")}
   <div class="rel"><div><h3>它从哪来</h3>${relLinks(i.up)}</div><div><h3>它引出了什么</h3>${relLinks(i.down)}</div></div></article>`}
function summary(t){ const xs=ofType(t), c=s=>xs.filter(i=>s.includes(i.status)).length;
  return {需求:`${c(["open","doing"])} 条还没解决 · ${c(["done","parked"])} 条已了结`,
   意图:`${xs.length} 个，${c(["doing"])} 个在推进`, 设计:c(["wait"])?`${c(["wait"])} 份等你确认`:`${xs.length} 份，都已确认`,
   任务:`在做 ${c(["doing"])} · 返工 ${c(["redo"])} · 做完 ${c(["done"])} · 没开始 ${c(["open"])}`,
   问题:`${xs.length} 个，${c(["done"])} 个当场处理了`, 决定:`${xs.length} 条，最近一条 ${xs.map(i=>i.date).sort().pop()||""}`}[t]}
function groups(t){ const xs=ofType(t).sort((a,b)=>(b.date||"").localeCompare(a.date||"")||b.id.localeCompare(a.id,undefined,{numeric:true}));
  const g=(name,sts)=>[name,xs.filter(i=>sts.includes(i.status))];
  return ({需求:[g("现在还没解决的",["open","doing"]),g("过去的",["done","parked"])],设计:[g("等你确认",["wait"]),g("已确认",["done"])],
   任务:[g("在做和返工",["doing","redo"]),g("没开始",["open"]),g("做完",["done"])],问题:[g("还没处理",["open"]),g("已处理",["done"])],
   意图:[g("在推进",["doing","open"]),g("已完成",["done"])],决定:[g("等确认",["wait"]),g("已定",["done"])]}[t]).filter(([,a])=>a.length)}
const lead = i => (i.fields.find(([k])=>["我们的理解","问题","现象","为什么","内容","步骤"].includes(k))||["",""])[1].replace(/```[\s\S]*?```/g,"").split("\n")[0].slice(0,70);
function now(){ const xs=Object.values(D.items);
  return {doing:xs.filter(i=>i.type==="任务"&&["doing","redo"].includes(i.status)), wait:xs.filter(i=>i.status==="wait"), open:xs.filter(i=>i.type==="需求"&&i.status==="open")}}
async function boot(render){ D=await (await fetch("/data.json")).json();
  const lb=document.createElement("div"); lb.id="lb"; lb.innerHTML="<img>"; document.body.appendChild(lb); lb.onclick=()=>lb.style.display="none";
  document.addEventListener("click",e=>{const im=e.target.closest(".detail figure img"); if(im){lb.querySelector("img").src=im.src; lb.style.display="flex"}});
  addEventListener("keydown",e=>{if(e.key==="Escape")lb.style.display="none"});
  const go=()=>{render(route()); window.scrollTo({top:0})}; addEventListener("hashchange",go); go()}
