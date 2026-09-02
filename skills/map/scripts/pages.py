"""serve proposal and review pages for the map skill

usage:
    python pages.py proposals <run_dir>
    python pages.py review <run_dir>

each command opens a local page and waits for feedback

proposals reads `proposals.json`:
    {
      "task": "short page title",
      "description": "optional context and preferred choice",
      "replies": ["optional answers to earlier notes"],
      "approaches": [{
        "title": "choice name",
        "summary": "one line",
        "complexity": "low",
        "steps": ["key change"],
        "pros": ["good part"],
        "cons": ["cost or risk"]
      }]
    }

it writes `feedback.json` with `picked`, `note`, and highlighted `comments`

review reads `diff.patch` plus optional `replies.json`, `summary.json`, and
`viewed.json`. run it from the repo so folded rows can show unchanged lines

it writes `review-feedback.json` with `verdict`, `note`, and `comments`
it also updates `viewed.json`

line comments use `file`, `line`, `side`, and `text`. ranges add `line_end`
and `side_end`. whole-file comments use line 0 and side `file`. summary
comments use an empty file, the round number as line, side `summary`, and a
highlighted `quote`. every review comment includes `round`. replies may use
`reply_to`

saved threads in `replies.json` may use `messages`, an ordered list of objects
with `author`, `text`, `round`, and an optional `quote`. use `you` for user
messages and `agent` for agent messages. preserve the list and append each new
user comment and agent reply for its round
"""

import hashlib
import json
import sys
import webbrowser
from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

STYLE = r"""
*{
box-sizing:border-box}
:root{
--bg:#faf9f6;
--surface:#ffffff;
--ink:#1f1e1a;
--ink-strong:#1f1e1a;
--body:#3d3a32;
--muted:#716c5f;
--faint:#a8a294;
--line:#e6e2d7;
--strong:#d8d3c6;
--accent:#4f6ef7;
--accent-ink:#fff;
--add:#eaf1e4;
--add-gutter:#deead6;
--add-gutter-ink:#8d9a84;
--del:#f8e9e4;
--del-gutter:#f1ddd5;
--hunk:#f1eee6;
--fold:#e8e4d9;
--lineno:#b6b0a1;
--plus:#3c7a4e;
--minus:#b8492f;
--mod:#c28418;
color-scheme:light}

html[data-theme=dark]{
--bg:#171613;
--surface:#1e1d19;
--ink:#eae6da;
--ink-strong:#f2eee2;
--body:#c9c4b4;
--muted:#928c7b;
--faint:#6e6a5d;
--line:#33312a;
--strong:#45423a;
--accent:#8fa1f8;
--accent-ink:#171613;
--add:#212a1c;
--add-gutter:#27331f;
--add-gutter-ink:#7a8a70;
--del:#2e211d;
--del-gutter:#382722;
--hunk:#24221d;
--fold:#26241e;
--lineno:#5c584d;
--plus:#8fbf9a;
--minus:#d9917c;
--mod:#cfa04a;
color-scheme:dark}

body{
margin:0;
background:var(--bg);
color:var(--ink);
font:15px/1.6 "Public Sans",system-ui,sans-serif;
padding-bottom:110px}
.sent{padding:0;user-select:none}
.sent .done{max-width:560px;margin:48px;padding:0}
.sent .done h1{font-size:46px;margin:0 0 18px}
.sent .done p{font-size:18px;color:var(--muted)}
.review{font-size:14px;padding-bottom:90px}
h1,h2,h3{
font-family:"Newsreader",Georgia,serif;
color:var(--ink-strong)}
header{
display:flex;
gap:20px;
align-items:center}
.proposals header{
padding:28px 56px 0;
align-items:flex-start;
justify-content:space-between;
flex-wrap:wrap}
.review header{
padding:18px 40px 14px;
border-bottom:1px solid var(--line);
position:sticky;
top:0;
background:var(--bg);
z-index:4;
align-items:flex-end;
flex-wrap:wrap}
.head{
margin-right:auto}
h1{
margin:0;
font:600 32px/1.15 "Newsreader",Georgia,serif;
letter-spacing:-.01em}
.proposals h1{
font-size:46px;
line-height:1.1;
margin:18px 0 10px}
.proposals .head{max-width:720px}
.review .head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.review .head small{width:100%}
.settings{
position:relative}
.settings>summary{
display:grid;
place-items:center;
width:40px;
height:40px;
border:0;
cursor:pointer;
list-style:none;
color:var(--ink);
user-select:none;
-webkit-user-select:none}
.settings>summary svg{
width:25px;
height:25px;
fill:none;
stroke:currentColor;
stroke-width:2;
stroke-linecap:round;
stroke-linejoin:round}
.settings>summary::-webkit-details-marker{
display:none}
.settings[open]>summary,.settings>summary:hover{
color:var(--accent)}
.settings-menu{
position:absolute;
top:38px;
left:0;
z-index:8;
display:grid;
gap:10px;
width:max-content;
min-width:0;
padding:10px;
background:var(--surface);
border:1px solid var(--strong);
box-shadow:0 8px 25px #0003}
.settings-menu .seg{
width:max-content;
justify-self:start}
.settings-menu label{
font-size:10px;
letter-spacing:.1em;
text-transform:uppercase;
color:var(--muted)}
.bar .settings-menu{
top:auto;
bottom:48px}
.totals{font:500 13px/1 "IBM Plex Mono",monospace;color:var(--muted)}
.plus{color:var(--plus)}
.minus{color:var(--minus)}
.review header input{width:180px;font-size:12px}
.hint,.desc{
color:var(--muted);
margin:4px 0;
white-space:pre-wrap}
.seg{
display:inline-flex;
flex:none;
border:1px solid var(--strong);
border-radius:99px;
overflow:hidden}
.seg button{
border:0;
border-radius:0;
padding:5px 11px;
min-width:64px;
white-space:nowrap}
.seg button.on{
background:var(--ink);
color:var(--bg)}
.seg button.on,.seg button.on:hover{
background:var(--ink)!important;
color:var(--bg)!important}
button{
font:inherit;
font-size:11px;
letter-spacing:.08em;
text-transform:uppercase;
border:1px solid var(--strong);
background:none;
color:var(--ink);
border-radius:99px;
padding:8px 16px;
cursor:pointer}
button:hover,button.primary{
background:var(--accent);
border-color:var(--accent);
color:var(--accent-ink)}
button.primary:hover{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
input,textarea{
font:inherit;
color:var(--ink);
background:none;
border:0;
border-bottom:1px solid var(--strong);
padding:6px 2px}
main.proposals{
position:relative;
max-width:832px;
margin:28px 56px 0}
.replies{
border-top:1px solid var(--line);
border-bottom:0;
padding:16px 0 18px}
.approach{
border-top:1px solid var(--line);
border-bottom:0;
padding:22px 0;
display:grid;
grid-template-columns:96px 1fr;
gap:28px}
.approach.picked{
box-shadow:inset 3px 0 var(--accent);
padding-left:20px;
margin-left:-20px}
.num{
font:400 56px/1 "Newsreader",Georgia,serif;
color:var(--faint)}
.approach.picked .num{color:var(--accent)}
.approach h2{
margin:0;
font:500 26px/1.2 "Newsreader",Georgia,serif}
.pk-pill{display:none;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;background:var(--accent);color:var(--accent-ink);border-radius:999px;padding:3px 10px;margin-left:12px;vertical-align:middle}
.approach.picked .pk-pill{display:inline-block}
.pk-pill{font-family:"Public Sans",system-ui,sans-serif;font-weight:600}
.approach>div>p{font-size:14.5px;margin:6px 0 14px}
.cols{
display:grid;
grid-template-columns:1fr 1fr 1fr;
gap:24px;
font-size:13.5px}
.cols h3,.replies h2,.summary h2{font:600 11px/1.4 "Public Sans",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.meta{
color:var(--muted);
font-size:12.5px}
mark{
background:color-mix(in srgb,var(--accent) 25%,transparent);
border-bottom:2px solid var(--accent);
color:inherit}
.comment-card{
border:1px solid var(--line);
border-left:2px solid var(--accent);
background:var(--surface);
padding:10px;
margin:6px 0;
max-width:100%;
overflow-wrap:anywhere}
.comment-card blockquote{
margin:0;
color:var(--muted)}
#rail{
position:absolute;
left:calc(100% + 24px);
top:0;
width:256px}
.proposal-note{
position:absolute;
left:0;
width:256px;
border-left:2px solid var(--accent);
border-top:1px solid var(--line);
border-right:1px solid var(--line);
border-bottom:1px solid var(--line);
padding:12px 14px;
background:var(--surface);
transition:top .15s,box-shadow .15s}
.proposal-note blockquote,.proposal-note p{margin:0 0 6px}
.proposal-note blockquote{font:italic 13px/1.5 "Newsreader",Georgia,serif;color:var(--muted)}
.proposal-note .remove{padding:2px 0;border:0}
.proposal-note.hot{box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 25%,transparent)}
mark.hot{background:color-mix(in srgb,var(--accent) 38%,transparent)}
.composer{
position:absolute;
width:280px;
background:var(--surface);
border:1px solid var(--strong);
padding:12px;
z-index:9;
box-shadow:0 8px 25px #0004}
.composer textarea{
width:100%;
min-height:70px}
.row{
display:flex;
justify-content:flex-end;
gap:7px;
margin-top:8px}
.bar{
position:fixed;
left:0;
right:0;
bottom:0;
background:var(--bg);
border-top:1px solid var(--line);
padding:14px 56px;
display:flex;
gap:12px;
align-items:center;
z-index:5}
.bar .status{
margin-right:auto;
color:var(--muted)}
.bar input{
width:300px}

.review-main{
display:flex;
align-items:flex-start}
.tree{
position:sticky;
top:102px;
width:248px;
min-width:180px;
max-width:50vw;
max-height:calc(100vh - 102px);
overflow:auto;
padding:18px 20px 24px;
flex:none}
.tree::after{
content:"";
position:absolute;
top:0;
right:-6px;
bottom:0;
width:12px;
cursor:col-resize;
touch-action:none;
z-index:2}
.tree #tree-toggle{
display:block;
width:100%;
min-width:0}
.tree #tree-search{
display:block;
width:100%;
min-width:0}
.tree.closed{
width:58px;
min-width:58px;
padding:18px 8px 24px;
overflow:hidden}
.tree.closed #tree-toggle{
height:38px;
padding:0}
.tree.closed .tree-body{
display:none}
.tree a{
display:flex;
gap:7px;
color:var(--ink);
text-decoration:none;
font:12.5px/1.4 "IBM Plex Mono",monospace;
padding:4px 0;
min-width:0}
.tree a span{
min-width:0;
overflow:hidden;
text-overflow:ellipsis;
white-space:nowrap}
.tree details{
margin-left:10px}
.tree details.root{
margin-left:0}
.tree summary{
cursor:pointer;
color:var(--muted);
font:12.5px/1.5 "IBM Plex Mono",monospace;
padding:3px 0;
list-style:none;
overflow:hidden;
text-overflow:ellipsis;
white-space:nowrap}
.tree summary::before{
content:"▸";
display:inline-block;
width:16px}
.tree details[open]>summary::before{
content:"▾"}
.tree-files{
margin-left:16px}
.dot{
width:7px;
height:7px;
border-radius:50%;
margin-top:5px;
flex:none}
.dot.added{
background:var(--plus)}
.dot.deleted{
background:var(--minus)}
.dot.modified{
background:var(--mod)}
.tree-file.viewed-file{
color:var(--faint);
opacity:.6}
.files{
min-width:0;
flex:1;
border-left:1px solid var(--line);
padding:18px 40px 40px 28px}
.summary{
border-bottom:1px solid var(--line);
padding-bottom:14px}
.summary details{
margin:6px}
.file{
margin-bottom:28px;
scroll-margin-top:calc(var(--review-header-height,101px) + 8px)}
.file h2{
font:500 13px/1.2 "IBM Plex Mono",monospace;
position:sticky;
top:var(--review-header-height,101px);
background:var(--bg);
z-index:3;
border-bottom:2px solid var(--line);
padding:8px 10px;
margin:0;
min-height:42px;
display:flex;
gap:10px;
align-items:center}
.file h2 .collapse{
width:28px;
height:28px;
padding:0;
flex:none}
.file-title,.status-pill,.file-lines,.viewed{
height:28px;
display:flex;
align-items:center}
.file-title{
font-weight:500;
white-space:nowrap}
.file-lines{
gap:7px;
font-size:11px}
.file h2 .file-note{
height:28px;
padding:0 14px}
.file.closed table{
display:none}
.file.closed .file-threads{
display:none}
.sp{
margin-left:auto}
.status-pill{
font-size:10px;
color:var(--muted)}
table{
width:100%;
border-collapse:collapse;
font:12.5px/1.6 "IBM Plex Mono",monospace}
td{
padding:0 8px;
vertical-align:top}
td.ln{
position:relative;
width:48px;
text-align:right;
color:var(--lineno);
user-select:none}
td.code{
white-space:pre-wrap;
word-break:break-all}
tr.add td.code{
background:var(--add)}
tr.add td.ln{
background:var(--add-gutter);
color:var(--add-gutter-ink)}
tr.del td.code{
background:var(--del)}
tr.del td.ln{
background:var(--del-gutter)}
tr.hunk td{
background:var(--hunk);
color:var(--muted)}
tr.fold td{
text-align:left;
background:var(--fold);
color:var(--muted);
text-transform:uppercase;
font:11px system-ui;
padding:3px 8px}
.fold-actions{
display:flex;
justify-content:flex-start;
gap:4px}
.fold-actions button{
width:24px;
height:24px;
border:1px solid var(--strong);
border-radius:4px;
padding:0;
font-size:14px;
line-height:1}
.split.select-old [data-side="new"],.split.select-new [data-side="old"]{
user-select:none;
-webkit-user-select:none}
.split{table-layout:fixed}
.split col.line{width:48px}
.split col.code{width:calc(50% - 48px)}
.split td:nth-child(2){border-right:1px solid var(--line)}
.split td.empty{background:var(--surface)!important}
.split td.code.add{background:var(--add)}
.split td.ln.add{background:var(--add-gutter);color:var(--add-gutter-ink)}
.split td.code.del{background:var(--del)}
.split td.ln.del{background:var(--del-gutter)}
.cbtn{
position:absolute;
inset:0;
display:none;
border:0;
border-radius:0;
padding:0}
.ln:hover .cbtn{
display:block}
.selected-side,.drag-selected{
box-shadow:inset 3px 0 var(--accent)!important}
.draft-note td{
padding:8px 12px;
background:var(--surface)}
.draft-note .comment-card{
width:100%;
max-width:none}
.draft-note .comment-thread{
width:100%}
.file-threads{
padding:10px 12px;
background:var(--surface);
border-bottom:1px solid var(--line)}
.file-threads .comment-card{
width:100%;
max-width:none}
.file-threads .comment-thread{
width:100%}
.comment-thread{
border-left:2px solid var(--accent);
margin:6px 0;
position:relative}
.thread-actions{
display:flex;
justify-content:flex-end;
gap:6px;
padding:5px 8px;
border:1px solid var(--line);
border-left:0;
background:var(--surface)}
.thread-actions button{
padding:2px 8px}
.comment-thread.collapsed .comment-card{
display:none}
.comment-thread.resolved{
display:none}
.comment-thread .comment-card{
margin:0;
border-left:0}
.comment-thread .comment-card+.comment-card{
border-top:0}
.comment-thread .reply,.comment-thread .reply-local{
display:none}
.comment-thread .comment-card:last-child .reply,.comment-thread .comment-card:last-child .reply-local{
display:inline-block}
.thread-composer textarea{
width:100%;
min-height:84px}
.thread-composer{
width:100%}
.comment-author{
font-weight:600;
margin-right:8px}
.draft-note textarea,.file-threads textarea{
width:100%;
min-height:84px}
.comment-preview{
font:12px/1.55 "IBM Plex Mono",monospace;
white-space:pre-wrap;
margin:0 0 8px;
padding:8px 10px;
background:var(--hunk);
border-left:3px solid var(--accent)}
.note-row td{
padding:0;
background:none;
min-width:0;
overflow:hidden}
.viewed{
gap:5px;
color:var(--muted);
font:12px system-ui;
cursor:pointer;
user-select:none;
-webkit-user-select:none}
.viewed input{
margin:0;
cursor:pointer}
.empty{
background:var(--surface)}

@media(max-width:800px){
.proposals header{
padding:18px 20px 0}
.proposals h1{
font-size:38px}
main.proposals{
margin:18px 20px 0}
.approach{
grid-template-columns:56px 1fr;
gap:12px;
padding:18px 0}
.num{
font-size:42px}
.cols{
grid-template-columns:1fr;
gap:8px}
.cols h3{
margin:8px 0 4px}
.cols ol,.cols ul{
margin:4px 0 10px;
padding-left:24px}
.tree{
display:none}
.files{
border:0;
padding:12px}
.split td.code{
width:auto}
header{
padding:14px}
.bar{
padding:10px}
.bar .status{
display:none}
.bar input{
width:auto;
min-width:0;
flex:1}
}

"""


BASE_JS = r"""
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];

async function post(data){
await fetch('/feedback',{
method:'POST',headers:{
'Content-Type':'application/json'}
,body:JSON.stringify(data)}
);
document.body.className='sent';
document.body.innerHTML='<main class="done"><h1>sent</h1><p>go back to your agent</p></main>'}

const theme=localStorage.getItem('map-theme')||'light';
document.documentElement.dataset.theme=theme;

$$('button[data-theme]').forEach(b=>{
b.classList.toggle('on',b.dataset.theme===theme);
b.onclick=()=>{
localStorage.setItem('map-theme',b.dataset.theme);
document.documentElement.dataset.theme=b.dataset.theme;
$$('button[data-theme]').forEach(x=>x.classList.toggle('on',x===b))}
}
);

document.addEventListener('click',event=>{
$$('.settings[open]').forEach(settings=>{
if(!settings.contains(event.target))settings.removeAttribute('open')})});

function composer(anchor,placeholder,save,cancel=()=>{}){
const previous=$('.composer');
if(previous)previous._cancel();
const box=document.createElement('div');
box.className='composer';
box.innerHTML='<textarea></textarea><div class="row"><button class="cancel">cancel</button><button class="primary save">save</button></div>';
box._cancel=()=>{cancel();box.remove()};
box.querySelector('textarea').placeholder=placeholder;
document.body.append(box);
const r=anchor.getBoundingClientRect();
box.style.left=Math.min(scrollX+r.right+8,innerWidth-295)+'px';
box.style.top=scrollY+r.top+'px';
box.querySelector('.cancel').onclick=box._cancel;
box.querySelector('.save').onclick=()=>{
const text=box.querySelector('textarea').value.trim();
if(text){
save(text);
box.remove()}
}
;
box.querySelector('textarea').onkeydown=e=>{
if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){
e.preventDefault();
box.querySelector('.save').click()}
else if(e.key==='Escape')box._cancel()}
;
box.querySelector('textarea').focus()}

function textNodesIn(range){
const root=range.commonAncestorContainer.nodeType===Node.TEXT_NODE?range.commonAncestorContainer.parentNode:range.commonAncestorContainer;
const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
const nodes=[];
for(let node=walker.nextNode();node;node=walker.nextNode()){
if(range.intersectsNode(node)&&node.textContent.trim())nodes.push(node)}
return nodes}

function markRange(range){
const marks=[];
for(const node of textNodesIn(range)){
let start=node===range.startContainer?range.startOffset:0;
let end=node===range.endContainer?range.endOffset:node.length;
if(start>=end)continue;
const part=document.createRange();
part.setStart(node,start);
part.setEnd(node,end);
const mark=document.createElement('mark');
part.surroundContents(mark);
marks.push(mark)}
return marks}

function unwrapMarks(marks){
for(const mark of marks||[]){
if(mark.isConnected)mark.replaceWith(...mark.childNodes)}}

"""


def theme_buttons() -> str:
    return '<span class="seg"><button data-theme="light">light</button><button data-theme="dark">dark</button></span>'


def settings_menu(include_view: bool = False) -> str:
    view = ""
    if include_view:
        view = '<label>diff view</label><span class="seg" id="view"><button data-view="inline">inline</button><button data-view="split" class="on">split</button></span>'
    gear = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></svg>'
    return f'<details class="settings"><summary aria-label="page settings">{gear}</summary><div class="settings-menu">{view}<label>theme</label>{theme_buttons()}</div></details>'


def page(title: str, mode: str, head: str, body: str, footer: str, script: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{
        escape(title)
    }
</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet"><script>document.documentElement.dataset.theme=localStorage.getItem('map-theme')||'light'</script><style>{
        STYLE
    }
</style></head><body class="{mode}"><header>{head}
</header>{body}
{footer}
<script>{BASE_JS}
\n{script}
</script></body></html>"""


def list_items(values: list[str]) -> str:
    return "".join(f"<li>{escape(str(value))}</li>" for value in values)


def render_proposals(data: dict) -> str:
    parts: list[str] = []
    if data.get("replies"):
        parts.append(
            f'<section class="replies"><h2>replies to your notes</h2><ul>{list_items(data["replies"])}</ul></section>'
        )
    for i, approach in enumerate(data["approaches"], 1):
        title = escape(str(approach["title"]))
        parts.append(
            f'''<article class="approach" data-title="{escape(str(approach["title"]), quote=True)}"><div class="num">{i}</div><div><h2>{title}<span class="pk-pill">picked</span></h2><p>{escape(str(approach.get("summary", "")))}</p><div class="cols"><div><h3>steps</h3><ol>{list_items(approach.get("steps", []))}</ol></div><div><h3>pros</h3><ul>{list_items(approach.get("pros", []))}</ul></div><div><h3>cons</h3><ul>{list_items(approach.get("cons", []))}</ul></div></div><p class="meta">complexity: {escape(str(approach.get("complexity", "?")))}</p><button class="pick">pick this</button></div></article>'''
        )
    desc = f'<p class="desc">{escape(str(data["description"]))}</p>' if data.get("description") else ""
    head = f'<div class="head"><small>map / proposals</small><h1>{escape(str(data["task"]))}</h1>{desc}<p class="hint">pick an approach, highlight any text to leave a note, then send</p></div>'
    body = f'<main class="proposals">{"".join(parts)}<aside id="rail"></aside></main>'
    footer = f'<footer class="bar">{settings_menu()}<span class="status">nothing picked yet</span><input id="overall" placeholder="overall note, optional"><button id="send" class="primary">send to agent</button></footer>'
    script = r"""let picked=null,comments=[],nextCommentId=1;
const commentMarks=new Map();
function renderProposalComments(){
const host=$('#rail');
host.innerHTML=comments.map(c=>`<article class="proposal-note" data-id="${c.id}"><blockquote>${c.quote.replaceAll('&','&amp;').replaceAll('<','&lt;')}</blockquote><p>${c.text.replaceAll('&','&amp;').replaceAll('<','&lt;')}</p><button class="ghost remove" data-id="${c.id}">remove</button></article>`).join('');
$$('.proposal-note .remove').forEach(b=>b.onclick=()=>{
const id=+b.dataset.id;
unwrapMarks(commentMarks.get(id));
commentMarks.delete(id);
comments=comments.filter(c=>c.id!==id);
renderProposalComments()});
layoutProposalNotes()}
function layoutProposalNotes(){
const main=$('main.proposals');
let bottom=0;
comments.map(c=>({c,mark:commentMarks.get(c.id)?.[0],card:$(`.proposal-note[data-id="${c.id}"]`)})).filter(x=>x.mark&&x.card).sort((a,b)=>a.mark.getBoundingClientRect().top-b.mark.getBoundingClientRect().top).forEach(x=>{
const wanted=Math.max(0,x.mark.getBoundingClientRect().top+scrollY-main.offsetTop);
const top=Math.max(wanted,bottom);
x.card.style.top=top+'px';
bottom=top+x.card.offsetHeight+10})}
addEventListener('resize',layoutProposalNotes);
document.addEventListener('mouseover',e=>{
const mark=e.target.closest('mark[data-comment-id]');
const card=e.target.closest('.proposal-note[data-id]');
const id=mark?.dataset.commentId||card?.dataset.id;
if(!id)return;
mark?.classList.add('hot');
card?.classList.add('hot');
commentMarks.get(+id)?.forEach(x=>x.classList.add('hot'));
$(`.proposal-note[data-id="${id}"]`)?.classList.add('hot')});
document.addEventListener('mouseout',e=>{
if(e.target.closest('mark[data-comment-id],.proposal-note[data-id]')){
$$('mark.hot,.proposal-note.hot').forEach(x=>x.classList.remove('hot'))}});
$$('.pick').forEach(b=>b.onclick=()=>{
const a=b.closest('.approach');
const unpick=picked===a.dataset.title;
picked=unpick?null:a.dataset.title;
$$('.approach').forEach(x=>x.classList.toggle('picked',!unpick&&x===a));
$$('.approach .pick').forEach(button=>button.textContent=button.closest('.approach').classList.contains('picked')?'unselect':'pick this');
$('.status').textContent=picked?'picked: '+picked:'nothing picked yet'}
);
document.addEventListener('mouseup',e=>{
if(document.body.classList.contains('sent'))return;
if(e.target.closest('button,.composer'))return;
const s=getSelection(),q=s.toString().trim();
if(!q)return;
const r=s.getRangeAt(0),marks=markRange(r);
if(!marks.length)return;
s.removeAllRanges();
composer(marks[0],'what should change here? (ctrl+enter saves)',text=>{
const id=nextCommentId++;
comments.push({id,quote:q.slice(0,400),text});
commentMarks.set(id,marks);
marks.forEach(mark=>mark.dataset.commentId=id);
renderProposalComments()
},()=>unwrapMarks(marks))}
);
$('#send').onclick=()=>post({
picked,note:$('#overall').value.trim(),comments:comments.map(({id,...comment})=>comment)}
);
"""
    return page(str(data["task"]), "proposals", head, body, footer, script)


def parse_diff(text: str) -> list[dict]:
    files: list[dict] = []
    current: dict | None = None
    in_hunk = False
    old_line = 0
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git"):
            current = {"path": raw.split(" b/")[-1], "rows": [], "status": "modified"}
            files.append(current)
            in_hunk = False
        elif current is None:
            continue
        elif raw.startswith("new file"):
            current["status"] = "added"
        elif raw.startswith("deleted file"):
            current["status"] = "deleted"
        elif raw.startswith("rename from"):
            current["status"] = "renamed"
        elif raw.startswith("@@"):
            cols = raw.split()
            old_line = int(cols[1].lstrip("-").split(",")[0])
            new_line = int(cols[2].lstrip("+").split(",")[0])
            in_hunk = True
            current["rows"].append(
                {
                    "kind": "hunk",
                    "old": "",
                    "new": "",
                    "text": raw,
                    "old_start": old_line,
                    "new_start": new_line,
                }
            )
        elif not in_hunk or raw.startswith("\\"):
            continue
        elif raw.startswith("+"):
            current["rows"].append({"kind": "add", "old": "", "new": new_line, "text": raw[1:]})
            new_line += 1
        elif raw.startswith("-"):
            current["rows"].append({"kind": "del", "old": old_line, "new": "", "text": raw[1:]})
            old_line += 1
        else:
            current["rows"].append({"kind": "ctx", "old": old_line, "new": new_line, "text": raw[1:]})
            old_line += 1
            new_line += 1
    return files


def tree_order(path: str) -> list[tuple[int, str]]:
    *dirs, name = path.split("/")
    return [(0, directory.lower()) for directory in dirs] + [(1, name.lower())]


def add_context(files: list[dict]) -> None:
    fold_id = 0
    for item in files:
        try:
            lines = Path(item["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        out: list[dict] = []
        next_old = 1
        next_new = 1
        for row in item["rows"]:
            if row["kind"] == "hunk":
                end = row["new_start"]
                if next_new < end:
                    fold_id += 1
                    edge = "start" if next_new == 1 else "between"
                    out.append(
                        {
                            "kind": "fold",
                            "edge": edge,
                            "start": next_new,
                            "end": end,
                            "fold": fold_id,
                            "off": row["old_start"] - row["new_start"],
                            "lines": lines[next_new - 1 : end - 1],
                        }
                    )
                out.append(row)
            else:
                out.append(row)
                if row["old"] != "":
                    next_old = int(row["old"]) + 1
                if row["new"] != "":
                    next_new = int(row["new"]) + 1
        if next_new <= len(lines):
            fold_id += 1
            out.append(
                {
                    "kind": "fold",
                    "edge": "end",
                    "start": next_new,
                    "end": len(lines) + 1,
                    "fold": fold_id,
                    "off": next_old - next_new,
                    "lines": lines[next_new - 1 :],
                }
            )
        item["rows"] = out


def review_data(task: str, files: list[dict], replies: list[dict], summary: list[str], viewed: dict) -> str:
    return json.dumps(
        {
            "task": task,
            "files": files,
            "replies": replies,
            "summary": summary,
            "viewed": viewed,
        }
    ).replace("</", "<\\/")


def render_review(task: str, files: list[dict], replies: list[dict], summary: list[str], viewed: dict) -> str:
    data = review_data(task, files, replies, summary, viewed)
    added = sum(1 for file in files for row in file["rows"] if row["kind"] == "add")
    deleted = sum(1 for file in files for row in file["rows"] if row["kind"] == "del")
    totals = f'{len(files)} file{"" if len(files) == 1 else "s"}, <span class="plus">+{added}</span> <span class="minus">-{deleted}</span>'
    head = f'<div class="head"><small>map / review</small><h1>{escape(task)}</h1><span class="totals">{totals}</span></div>'
    body = '<main class="review-main"><nav class="tree"><button id="tree-toggle" aria-expanded="true">files</button><div class="tree-body"><input id="tree-search" placeholder="search files"></div></nav><div class="files"><section class="summary"></section><div id="file-list"></div></div></main>'
    footer = f'<footer class="bar">{settings_menu(include_view=True)}<span class="status">review changes</span><input id="overall" placeholder="overall note, optional"><button id="changes">request changes</button><button id="approve" class="primary">approve</button></footer>'
    script = (
        r"""const DATA="""
        + data
        + r""";
let comments=[],nextCommentId=1,view='split',viewed={
...DATA.viewed}
;
let nextLogicalRowId=1;
DATA.files.forEach(file=>file.rows.forEach(row=>row._key=`row-${nextLogicalRowId++}`));
const esc=s=>{
const d=document.createElement('div');
d.textContent=s;
return d.innerHTML}
;
const attr=s=>esc(s).replaceAll('"','&quot;').replaceAll("'",'&#39;');
const data=(element,name)=>(element.dataset[name]||'').trim();
const commentViews=new Map();
const collapsedThreads=new Set(),resolvedThreads=new Set();
const currentRound=Math.max(1,DATA.summary.length);
let dragStart=null,dragRows=[];
let textSelectionSide=null,textSelectionPointer=false,adjustingTextSelection=false;

function threadKey(reply){return DATA.replies.indexOf(reply)}

function messageAuthor(message){
return message.author==='agent'||message.author==='assistant'?'agent':'you'}

function threadHtml(reply,file,line,side){
const key=threadKey(reply);
const classes=`comment-thread${collapsedThreads.has(key)?' collapsed':''}${resolvedThreads.has(key)?' resolved':''}`;
const messages=reply.messages||[{author:'you',text:reply.reply_to,quote:reply.quote},{author:'agent',text:reply.text}];
const cards=messages.filter(message=>message.text).map((message,index)=>{
const preview=message.quote?`<pre class="comment-preview">${esc(message.quote)}</pre>`:'';
const round=message.round||reply.round||currentRound;
const replyButton=index===messages.length-1?`<button class="reply" data-reply="${key}" data-file="${attr(file)}" data-line="${line}" data-side="${side}" data-round="${round}">reply</button>`:'';
return `<div class="comment-card"><span class="comment-author">${messageAuthor(message)}</span>${preview}<p>${esc(message.text)}</p>${replyButton}</div>`}).join('');
return `<div class="${classes}" data-thread="${key}"><div class="thread-actions"><button class="collapse-thread">${collapsedThreads.has(key)?'expand':'collapse'}</button><button class="resolve-thread">resolve</button></div>${cards}</div>`}

function notes(file,line,side){
return DATA.replies.filter(r=>r.file===file&&+r.line===+line&&(r.side||'new')===side).map(r=>`<tr class="note-row">${reviewCells(side,threadHtml(r,file,line,side))}</tr>`).join('')}

function rowReplies(file,row){
const locations=[];
if(row.kind==='ctx')locations.push(['old',row.old],['new',row.new]);
else if(row.kind==='del')locations.push(['old',row.old]);
else if(row.kind==='add')locations.push(['new',row.new]);
return locations.flatMap(([side,line])=>DATA.replies.map((reply,index)=>({reply,index,side,line})).filter(item=>item.reply.file===file&&+item.reply.line===+line&&(item.reply.side||'new')===side))}

function fileThreads(file){
const replies=DATA.replies.filter(r=>r.file===file&&+r.line===0&&(r.side||'file')==='file');
if(!replies.length)return '';
return `<div class="file-threads">${replies.map(r=>threadHtml(r,file,0,'file')).join('')}</div>`}

function targetsBetween(first,last){
if(!first||!last||data(first,'side')!==data(last,'side'))return [];
const scope=first.closest('.file');
if(!scope||scope!==last.closest('.file'))return [];
const targets=$$(`td.code[data-side="${data(first,'side')}"]`,scope);
let start=targets.indexOf(first),end=targets.indexOf(last);
if(start>end)[start,end]=[end,start];
return targets.slice(start,end+1)}

function clearDrag(){
dragRows.forEach(target=>target.classList.remove('drag-selected'));
dragRows=[]}

function showDrag(first,last){
clearDrag();
dragRows=targetsBetween(first,last);
dragRows.forEach(target=>target.classList.add('drag-selected'))}

function removeReviewComment(id){
const view=commentViews.get(id);
unwrapMarks(view?.marks);
view?.targets.forEach(target=>target.classList.remove('selected-side'));
$$(`[data-comment-id="${id}"]`).forEach(element=>element.remove());
commentViews.delete(id);
comments=comments.filter(comment=>comment.id!==id&&comment.thread!==id)}

function localRepliesFor(comment){
return comments.filter(reply=>reply.reply_to&&reply.thread===comment.id)}

function localThreadHtml(comment,removeClass){
const preview=comment.quote?`<pre class="comment-preview">${esc(comment.quote)}</pre>`:'';
const replies=localRepliesFor(comment).map(reply=>`<div class="comment-card local-reply" data-comment-id="${reply.id}"><span class="comment-author">you</span><p>${esc(reply.text)}</p><button class="reply-local">reply</button></div>`).join('');
return `<div class="comment-thread"><div class="comment-card"><span class="comment-author">you</span>${preview}<p>${esc(comment.text)}</p><button class="reply-local">reply</button><button class="${removeClass}" data-comment-id="${comment.id}">remove</button></div>${replies}</div>`}

function bindLocalThread(host,comment){
const thread=$('.comment-thread',host),latest=localRepliesFor(comment).at(-1)||comment;
$$('.reply-local',host).at(-1).onclick=()=>openThreadReply(thread,latest.text,{file:comment.file,line:comment.line,side:comment.side,thread:comment.id,round:comment.round||currentRound});
$(`[data-comment-id="${comment.id}"].remove-draft`,host)?.addEventListener('click',()=>removeReviewComment(comment.id));
$(`[data-comment-id="${comment.id}"].remove-file`,host)?.addEventListener('click',()=>removeReviewComment(comment.id))}

function restoreReviewComments(){
const cells=$$('td.code[data-side][data-line]');
comments.filter(comment=>!comment.reply_to&&(comment.side==='old'||comment.side==='new')).forEach(comment=>{
const findCell=line=>cells.find(cell=>data(cell.closest('tr'),'file')===comment.file&&data(cell,'side')===comment.side&&+data(cell,'line')===+line);
const first=findCell(comment.line),last=findCell(comment.line_end||comment.line);
const targets=targetsBetween(first,last);
if(!targets.length)return;
targets.forEach(target=>target.classList.add('selected-side'));
commentViews.set(comment.id,{targets,marks:[]});
const card=localThreadHtml(comment,'remove-draft');
const draft=insertReviewRow(last.closest('tr'),comment.side,card,'draft-note',comment.id);
bindLocalThread(draft,comment)})}

function restoreFileComments(){
comments.filter(comment=>!comment.reply_to&&comment.side==='file').forEach(comment=>{
const fileIndex=DATA.files.findIndex(file=>file.path===comment.file),section=$(`#f-${fileIndex}`);
if(!section)return;
let host=$('.file-threads',section);
if(!host){
section.querySelector('h2').insertAdjacentHTML('afterend','<div class="file-threads"></div>');
host=$('.file-threads',section)}
host.insertAdjacentHTML('beforeend',`<div class="local-file" data-comment-id="${comment.id}">${localThreadHtml(comment,'remove-file')}</div>`);
bindLocalThread($(`.local-file[data-comment-id="${comment.id}"]`,host),comment)})}

function restoreSummaryComments(){
comments.filter(comment=>!comment.reply_to&&comment.side==='summary').forEach(comment=>{
const paragraph=$(`.summary p[data-round="${comment.line}"]`);
if(!paragraph)return;
const preview=comment.quote?`<pre class="comment-preview">${esc(comment.quote)}</pre>`:'';
paragraph.insertAdjacentHTML('afterend',`<article class="comment-card summary-comment" data-comment-id="${comment.id}">${preview}<p>${esc(comment.text)}</p><button class="remove-summary" data-comment-id="${comment.id}">remove</button></article>`);
$('.remove-summary',paragraph.nextElementSibling).onclick=()=>removeReviewComment(comment.id)})}

function openThreadReply(thread,original,location){
$('.thread-composer',thread)?.remove();
thread.insertAdjacentHTML('beforeend','<div class="comment-card thread-composer"><textarea placeholder="reply to this comment"></textarea><div class="row"><button class="cancel">cancel</button><button class="primary save">save</button></div></div>');
const box=$('.thread-composer',thread),textarea=$('textarea',box);
$('.cancel',box).onclick=()=>box.remove();
$('.save',box).onclick=()=>{
const text=textarea.value.trim();
if(!text)return;
const id=nextCommentId++;
comments.push({id,...location,text,reply_to:original});
box.outerHTML=`<div class="comment-card local-reply" data-comment-id="${id}"><span class="comment-author">you</span><p>${esc(text)}</p><button class="reply-local">reply</button></div>`;
const card=$(`.local-reply[data-comment-id="${id}"]`,thread);
$('.reply-local',card).onclick=()=>openThreadReply(thread,text,location)};
textarea.onkeydown=event=>{
if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){
event.preventDefault();
$('.save',box).click()}
else if(event.key==='Escape')box.remove()};
textarea.focus()}

function commentOnFile(button){
const section=button.closest('.file'),file=data(button,'file');
let host=$('.file-threads',section);
if(!host){
section.querySelector('h2').insertAdjacentHTML('afterend','<div class="file-threads"></div>');
host=$('.file-threads',section)}
host.insertAdjacentHTML('beforeend','<div class="comment-thread pending-file"><div class="comment-card"><textarea placeholder="comment on this file"></textarea><div class="row"><button class="cancel">cancel</button><button class="primary save">save</button></div></div></div>');
const pending=$('.pending-file',host),textarea=$('textarea',pending);
$('.cancel',pending).onclick=()=>pending.remove();
$('.save',pending).onclick=()=>{
const text=textarea.value.trim();
if(!text)return;
const id=nextCommentId++;
comments.push({id,thread:id,file,line:0,side:'file',round:currentRound,text});
pending.outerHTML=`<div class="comment-thread local-file" data-comment-id="${id}"><div class="comment-card"><span class="comment-author">you</span><p>${esc(text)}</p><button class="reply-local">reply</button><button class="remove-file">remove</button></div></div>`;
const thread=$(`.local-file[data-comment-id="${id}"]`,host);
$('.reply-local',thread).onclick=()=>openThreadReply(thread,text,{file,line:0,side:'file',thread:id,round:currentRound},thread);
$('.remove-file',thread).onclick=()=>{
thread.remove();
comments=comments.filter(comment=>comment.id!==id&&comment.thread!==id)}
};
textarea.onkeydown=event=>{
if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){
event.preventDefault();
$('.save',pending).click()}
else if(event.key==='Escape')pending.remove()};
textarea.focus()}

function reviewCells(side,content){
if(view==='inline')return `<td colspan="4">${content}</td>`;
if(side==='old')return `<td colspan="2">${content}</td><td colspan="2"></td>`;
return `<td colspan="2"></td><td colspan="2">${content}</td>`}

function insertReviewRow(afterRow,side,content,className,commentId=''){
afterRow.insertAdjacentHTML('afterend',`<tr class="${className}" data-comment-id="${commentId}">${reviewCells(side,content)}</tr>`);
return afterRow.nextElementSibling}

function removeReviewRow(row){
row.remove()}

function saveReviewComment(targets,marks,quote,text){
const first=targets[0],last=targets.at(-1),id=nextCommentId++;
const firstRow=first.closest('tr'),lastRow=last.closest('tr');
const side=data(first,'side');
const comment={id,thread:id,file:data(firstRow,'file'),line:+data(first,'line'),side,round:currentRound,text};
if(last!==first){
comment.line_end=+data(last,'line');
comment.side_end=side}
if(quote)comment.quote=quote.slice(0,400);
comments.push(comment);
targets.forEach(target=>target.classList.add('selected-side'));
marks.forEach(mark=>mark.dataset.commentId=id);
commentViews.set(id,{targets,marks});
const preview=quote?`<pre class="comment-preview">${esc(quote.slice(0,400))}</pre>`:'';
const card=`<div class="comment-thread"><div class="comment-card"><span class="comment-author">you</span>${preview}<p>${esc(text)}</p><button class="reply-local">reply</button><button class="remove-draft" data-comment-id="${id}">remove</button></div></div>`;
const draft=insertReviewRow(lastRow,side,card,'draft-note',id),thread=$('.comment-thread',draft);
$('.reply-local',draft).onclick=()=>openThreadReply(thread,text,{file:comment.file,line:comment.line,side:comment.side,thread:id,round:currentRound},draft);
$(`.remove-draft[data-comment-id="${id}"]`).onclick=()=>removeReviewComment(id)}

function commentOnTargets(targets,marks=[],quote=''){
if(!targets.length)return;
$('.pending-note .cancel')?.click();
const side=data(targets[0],'side'),lastRow=targets.at(-1).closest('tr');
const preview=quote?`<pre class="comment-preview">${esc(quote.slice(0,400))}</pre>`:'';
const editor=`<div class="comment-card">${preview}<textarea placeholder="leave a note on this selection"></textarea><div class="row"><button class="cancel">cancel</button><button class="primary save">save</button></div></div>`;
const pending=insertReviewRow(lastRow,side,editor,'draft-note pending-note');
const cancel=()=>{
clearDrag();
unwrapMarks(marks);
removeReviewRow(pending)};
$('.cancel',pending).onclick=cancel;
$('.save',pending).onclick=()=>{
const text=$('textarea',pending).value.trim();
if(!text)return;
removeReviewRow(pending);
clearDrag();
saveReviewComment(targets,marks,quote,text)};
$('textarea',pending).onkeydown=e=>{
if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){
e.preventDefault();
$('.save',pending).click()}
else if(e.key==='Escape')cancel()};
$('textarea',pending).focus()}

function foldControls(r){
const down=r.edge!=='start'?'<button data-expand="down" aria-label="expand downward">↓</button>':'';
const up=r.edge!=='end'?'<button data-expand="up" aria-label="expand upward">↑</button>':'';
return `<span class="fold-actions">${down}${up}</span>`}

function rowHtml(f,r){
if(r.kind==='hunk')return `<tr class="hunk"><td colspan="4">${
esc(r.text)}
</td></tr>`;
if(r.kind==='fold')return `<tr class="fold" data-file="${
attr(f.path)}
" data-fold="${
r.fold}
"><td colspan="4">${foldControls(r)}</td></tr>`;
const side=r.kind==='del'?'old':'new',line=side==='old'?r.old:r.new,old=r.old||'',nw=r.new||'';
const button=(targetSide,targetLine)=>`<button class="cbtn" title="comment" data-side="${targetSide}" data-line="${targetLine}">+</button>`;
if(view==='inline')return `<tr class="${
r.kind}
" data-file="${
attr(f.path)}
" data-line="${
line}
" data-side="${
side}
"><td class="ln">${
old}
${
button(side,line)}
</td><td class="ln">${
nw}
</td><td class="code" colspan="2" data-side="${side}" data-line="${line}">${
esc(r.text)}
</td></tr>${
r.kind==='ctx'?notes(f.path,r.old,'old')+notes(f.path,r.new,'new'):notes(f.path,line,side)}
`;
if(r.kind==='del')return `<tr class="del" data-file="${
attr(f.path)}
" data-line="${
line}
" data-side="old"><td class="ln">${
old}
${
button('old',old)}
</td><td class="code" data-side="old" data-line="${old}">${
esc(r.text)}
</td><td class="ln empty"></td><td class="code empty"></td></tr>${
notes(f.path,line,'old')}
`;
if(r.kind==='add')return `<tr class="add" data-file="${attr(f.path)}" data-line="${nw}" data-side="new"><td class="ln empty"></td><td class="code empty"></td><td class="ln">${nw}${button('new',nw)}</td><td class="code" data-side="new" data-line="${nw}">${esc(r.text)}</td></tr>${notes(f.path,nw,'new')}`;
return `<tr class="ctx" data-file="${attr(f.path)}"><td class="ln">${old}${button('old',old)}</td><td class="code" data-side="old" data-line="${old}">${esc(r.text)}</td><td class="ln">${nw}${button('new',nw)}</td><td class="code" data-side="new" data-line="${nw}">${esc(r.text)}</td></tr>${notes(f.path,nw,'new')}`}

function splitRows(rows){
const pairs=[];
for(let i=0;i<rows.length;){
const row=rows[i];
if(row.kind==='del'||row.kind==='add'){
const block=[];
while(i<rows.length&&(rows[i].kind==='del'||rows[i].kind==='add'))block.push(rows[i++]);
const oldRows=block.filter(row=>row.kind==='del');
const newRows=block.filter(row=>row.kind==='add');
const count=Math.max(oldRows.length,newRows.length);
for(let index=0;index<count;index++){
const pair={old:oldRows[index]||null,new:newRows[index]||null};
pair.key=`pair-${pair.old?._key||'blank'}-${pair.new?._key||'blank'}`;
pairs.push(pair)}
continue}
pairs.push({old:row,new:row,key:row._key});
i++}
return pairs}

function splitRowHtml(f,pair){
const row=pair.old||pair.new;
if(row.kind==='hunk')return `<tr class="hunk"><td colspan="4">${esc(row.text)}</td></tr>`;
if(row.kind==='fold')return `<tr class="fold" data-file="${attr(f.path)}" data-fold="${row.fold}"><td colspan="4">${foldControls(row)}</td></tr>`;
const cell=(item,side)=>{
if(!item)return `<td class="ln empty" data-side="${side}"></td><td class="code empty" data-side="${side}"></td>`;
const line=side==='old'?item.old:item.new;
const button=`<button class="cbtn" title="comment" data-side="${side}" data-line="${line}">+</button>`;
return `<td class="ln ${item.kind}" data-side="${side}">${line}${button}</td><td class="code ${item.kind}" data-side="${side}" data-line="${line}">${esc(item.text)}</td>`};
const rows=pair.old===pair.new?[pair.old]:[pair.old,pair.new].filter(Boolean);
const replies=rows.flatMap(item=>rowReplies(f.path,item)).map(item=>`<tr class="note-row">${reviewCells(item.side,threadHtml(item.reply,f.path,item.line,item.side))}</tr>`).join('');
return `<tr data-file="${attr(f.path)}" data-row-key="${pair.key}">${cell(pair.old,'old')}${cell(pair.new,'new')}</tr>${replies}`}

function splitFileHtml(f){
return `<table class="split"><colgroup><col class="line"><col class="code"><col class="line"><col class="code"></colgroup><tbody>${splitRows(f.rows).map(pair=>splitRowHtml(f,pair)).join('')}</tbody></table>`}

function fileTree(files){
const root={dirs:new Map(),files:[]};
files.forEach((file,index)=>{
const parts=file.path.split('/');
const name=parts.pop();
let node=root;
for(const part of parts){
if(!node.dirs.has(part))node.dirs.set(part,{dirs:new Map(),files:[]});
node=node.dirs.get(part)}
node.files.push({name,index,file})});
const branch=(node,isRoot=false,prefix='')=>{
const directory=(name,child)=>{
const names=[name];
let path=prefix?prefix+'/'+name:name;
while(!child.files.length&&child.dirs.size===1){
const [nextName,nextChild]=child.dirs.entries().next().value;
names.push(nextName);
path+='/'+nextName;
child=nextChild}
return `<details open><summary title="${attr(path)}">${esc(names.join('/'))}</summary>${branch(child,false,path)}</details>`};
const dirs=[...node.dirs.entries()].sort(([a],[b])=>a.localeCompare(b)).map(([name,child])=>directory(name,child)).join('');
const leaves=node.files.sort((a,b)=>a.name.localeCompare(b.name)).map(item=>`<a class="tree-file${viewed[item.file.path]===item.file.hash?' viewed-file':''}" href="#f-${item.index}" title="${attr(item.file.path)}" data-index="${item.index}" data-path="${attr(item.file.path.toLowerCase())}"><i class="dot ${item.file.status}"></i><span>${esc(item.name)}</span></a>`).join('');
return `<div class="tree-files${isRoot?' root':''}">${dirs}${leaves}</div>`};
return branch(root,true)}

function render(){
const tree=$('.tree-body');
tree.innerHTML='<input id="tree-search" placeholder="search files">'+fileTree(DATA.files);
$('#file-list').innerHTML=DATA.files.map((f,i)=>{
const collapsed=viewed[f.path]===f.hash?' closed':'';
const added=f.rows.filter(row=>row.kind==='add').length;
const deleted=f.rows.filter(row=>row.kind==='del').length;
return `<section class="file${collapsed}" id="f-${i}"><h2><button class="collapse">${collapsed?'▸':'▾'}</button><span class="file-title">${
attr(f.path)}
 </span><span class="status-pill">${
f.status}
</span><span class="file-lines"><span class="plus">+${added}</span><span class="minus">-${deleted}</span></span><span class="sp"></span><label class="viewed"><input type="checkbox" data-file="${
attr(f.path)}
" ${
viewed[f.path]===f.hash?'checked':''}
>viewed</label><button class="file-note" data-file="${
attr(f.path)}
">comment</button></h2>${fileThreads(f.path)}${view==='inline'?`<table class="inline">${f.rows.map(r=>rowHtml(f,r)).join('')}</table>`:splitFileHtml(f)}</section>`}
).join('');
$('.summary').innerHTML=DATA.summary.length?'<h2>what changed</h2>'+DATA.summary.map((s,i)=>`<details ${
i===DATA.summary.length-1?'open':''}
><summary>round ${
i+1}
</summary><p data-round="${
i+1}
">${
esc(s)}
</p></details>`).join(''):'';
restoreReviewComments();
restoreFileComments();
restoreSummaryComments();
bind()}

function setCollapsed(section,collapsed){
section.classList.toggle('closed',collapsed);
$('.collapse',section).textContent=collapsed?'▸':'▾'}

function bind(){
$$('.collapse-thread').forEach(button=>button.onclick=()=>{
const thread=button.closest('.comment-thread'),key=+thread.dataset.thread;
const collapsed=!thread.classList.contains('collapsed');
thread.classList.toggle('collapsed',collapsed);
button.textContent=collapsed?'expand':'collapse';
if(collapsed)collapsedThreads.add(key);
else collapsedThreads.delete(key)});
$$('.resolve-thread').forEach(button=>button.onclick=()=>{
const thread=button.closest('.comment-thread'),key=+thread.dataset.thread;
resolvedThreads.add(key);
thread.classList.add('resolved')});
$$('.collapse').forEach(b=>b.onclick=()=>{
const section=b.closest('.file');
setCollapsed(section,!section.classList.contains('closed'))});
$$('.viewed input').forEach(x=>x.onchange=()=>{
const file=data(x,'file');
const f=DATA.files.find(y=>y.path===file);
const section=x.closest('.file');
const treeFile=$(`.tree-file[data-index="${DATA.files.indexOf(f)}"]`);
if(x.checked){
viewed[f.path]=f.hash;
treeFile?.classList.add('viewed-file');
setCollapsed(section,true)}
else{
delete viewed[f.path];
treeFile?.classList.remove('viewed-file');
setCollapsed(section,false)}}
);
$$('.file-note').forEach(b=>b.onclick=()=>commentOnFile(b));
$$('.cbtn').forEach(b=>b.onpointerdown=e=>{
e.preventDefault();
dragStart=$(`.code[data-side="${data(b,'side')}"]`,b.closest('tr'));
if(dragStart)showDrag(dragStart,dragStart)});
$$('.fold [data-expand]').forEach(button=>button.onclick=()=>{
const x=button.closest('.fold');
const f=DATA.files.find(y=>y.path===data(x,'file'));
const r=f.rows.find(y=>+y.fold===+data(x,'fold'));
const count=Math.min(12,r.lines.length);
let start,chunk,insertAt;
if(button.dataset.expand==='down'){
start=r.start;
chunk=r.lines.splice(0,count);
r.start+=count;
insertAt=f.rows.indexOf(r)}
else{
start=r.end-count;
chunk=r.lines.splice(-count);
r.end-=count;
insertAt=f.rows.indexOf(r)+1}
const expanded=chunk.map((text,i)=>({kind:'ctx',old:start+i+(r.off||0),new:start+i,text,_key:`row-${nextLogicalRowId++}`}));
f.rows.splice(insertAt,0,...expanded);
if(!r.lines.length)f.rows.splice(f.rows.indexOf(r),1);
$('.pending-note .cancel')?.click();
render()}
);
$$('.reply').forEach(b=>b.onclick=()=>{
const r=DATA.replies[+b.dataset.reply];
const latest=r.messages?.at(-1)?.text||r.text;
openThreadReply(b.closest('.comment-thread'),latest,{
file:data(b,'file'),line:+data(b,'line'),side:data(b,'side'),round:+data(b,'round')||currentRound},b)}
);
$$('.summary p').forEach(p=>p.onmouseup=e=>{
e.stopPropagation();
const selection=getSelection(),quote=selection.toString().trim();
if(!quote)return;
const marks=markRange(selection.getRangeAt(0));
selection.removeAllRanges();
composer(marks[0]||p,'comment on this round',text=>{
const id=nextCommentId++;
comments.push({id,thread:id,file:'',line:+p.dataset.round,side:'summary',round:+p.dataset.round,quote:quote.slice(0,400),text});
marks.forEach(mark=>mark.dataset.commentId=id);
p.insertAdjacentHTML('afterend',`<article class="comment-card summary-comment" data-comment-id="${id}"><pre class="comment-preview">${esc(quote.slice(0,400))}</pre><p>${esc(text)}</p><button class="remove-summary" data-comment-id="${id}">remove</button></article>`);
$(`.remove-summary[data-comment-id="${id}"]`).onclick=()=>{
unwrapMarks(marks);
$(`.summary-comment[data-comment-id="${id}"]`)?.remove();
comments=comments.filter(comment=>comment.id!==id&&comment.thread!==id)}
},()=>unwrapMarks(marks))}
);
$$('.tree-file').forEach(link=>link.onclick=e=>{
e.preventDefault();
const target=$(`#f-${data(link,'index')}`);
if(!target)return;
const headerHeight=document.querySelector('.review>header').offsetHeight;
const top=scrollY+target.getBoundingClientRect().top-headerHeight-8;
scrollTo({top,behavior:'auto'})});
$('#tree-search').oninput=e=>{
const query=e.target.value.trim().toLowerCase();
$$('.tree-file').forEach(link=>link.style.display=data(link,'path').includes(query)?'':'none');
$$('.tree details').reverse().forEach(folder=>{
const visible=$$('.tree-file',folder).some(link=>link.style.display!=='none');
folder.style.display=visible?'':'none';
if(query&&visible)folder.open=true})}}

$('#tree-toggle').onclick=()=>{
const tree=$('.tree'),closed=tree.classList.toggle('closed');
$('#tree-toggle').textContent=closed?'>':'files';
$('#tree-toggle').setAttribute('aria-expanded',String(!closed))};
{
const tree=$('.tree');
let resizing=false,startX=0,startWidth=0,lastWidth=tree.offsetWidth;
tree.addEventListener('pointerdown',event=>{
const edge=tree.getBoundingClientRect().right;
if(Math.abs(event.clientX-edge)>8)return;
event.preventDefault();
resizing=true;
startX=event.clientX;
startWidth=tree.offsetWidth;
tree.setPointerCapture(event.pointerId);
document.body.style.cursor='col-resize';
document.body.style.userSelect='none'});
tree.addEventListener('pointermove',event=>{
if(!resizing)return;
const width=startWidth+event.clientX-startX;
if(width<=90){
tree.classList.add('closed');
$('#tree-toggle').textContent='>';
$('#tree-toggle').setAttribute('aria-expanded','false');
return}
tree.classList.remove('closed');
lastWidth=Math.min(width,innerWidth/2);
tree.style.width=lastWidth+'px';
$('#tree-toggle').textContent='files';
$('#tree-toggle').setAttribute('aria-expanded','true')});
tree.addEventListener('pointerup',event=>{
if(!resizing)return;
resizing=false;
tree.releasePointerCapture(event.pointerId);
document.body.style.cursor='';
document.body.style.userSelect=''});
$('#tree-toggle').addEventListener('click',()=>{
if(!tree.classList.contains('closed'))tree.style.width=lastWidth+'px'})}
document.addEventListener('pointerdown',event=>{
const code=event.target.closest('.split td.code[data-side]');
$$('.split.select-old,.split.select-new').forEach(split=>split.classList.remove('select-old','select-new'));
textSelectionPointer=Boolean(code);
textSelectionSide=null;
if(!code)return;
textSelectionSide=data(code,'side');
const split=code.closest('.split');
split.classList.add(data(code,'side')==='old'?'select-old':'select-new')});
document.addEventListener('selectionchange',()=>{
const selection=getSelection();
if(!selection.rangeCount||selection.isCollapsed){
if(!textSelectionPointer)clearSplitSelection();
return}
if(!textSelectionSide||adjustingTextSelection)return;
const focusNode=selection.focusNode;
const focusElement=focusNode?.nodeType===Node.TEXT_NODE?focusNode.parentElement:focusNode;
const focusCell=focusElement?.closest?.('.split td.code[data-side]');
if(focusCell&&data(focusCell,'side')===textSelectionSide)return;
const focusRow=focusElement?.closest?.('tr[data-row-key]');
const cell=focusRow?$(`td.code[data-side="${textSelectionSide}"]`,focusRow):null;
if(!cell){selection.removeAllRanges();return}
const walker=document.createTreeWalker(cell,NodeFilter.SHOW_TEXT);
const nodes=[];
for(let node=walker.nextNode();node;node=walker.nextNode())nodes.push(node);
if(!nodes.length){selection.removeAllRanges();return}
const focusFollows=selection.anchorNode.compareDocumentPosition(focusElement)&Node.DOCUMENT_POSITION_FOLLOWING;
const boundary=focusFollows?nodes.at(-1):nodes[0],offset=focusFollows?boundary.length:0;
adjustingTextSelection=true;
selection.setBaseAndExtent(selection.anchorNode,selection.anchorOffset,boundary,offset);
adjustingTextSelection=false});
document.addEventListener('copy',event=>{
if(!textSelectionSide)return;
const selection=getSelection();
if(!selection.rangeCount||selection.isCollapsed)return;
const range=selection.getRangeAt(0),parts=[];
$$(`.split td.code[data-side="${textSelectionSide}"]`).forEach(cell=>{
if(!range.intersectsNode(cell))return;
const part=document.createRange();
part.selectNodeContents(cell);
if(range.compareBoundaryPoints(Range.START_TO_START,part)>0)part.setStart(range.startContainer,range.startOffset);
if(range.compareBoundaryPoints(Range.END_TO_END,part)<0)part.setEnd(range.endContainer,range.endOffset);
parts.push(part.toString())});
event.preventDefault();
event.clipboardData.setData('text/plain',parts.join('\n'))});
document.addEventListener('pointermove',event=>{
if(!dragStart)return;
const gutter=event.target.closest('td.ln'),button=gutter?.querySelector('.cbtn');
if(!button||data(button,'side')!==data(dragStart,'side'))return;
const target=$(`.code[data-side="${data(button,'side')}"]`,gutter.closest('tr'));
if(target&&targetsBetween(dragStart,target).length)showDrag(dragStart,target)});
const clearSplitSelection=()=>{
$$('.split.select-old,.split.select-new').forEach(split=>split.classList.remove('select-old','select-new'));
textSelectionSide=null};
const cancelPointerSelection=()=>{
dragStart=null;
textSelectionPointer=false;
clearDrag();
clearSplitSelection()};
document.addEventListener('pointerup',event=>{
textSelectionPointer=false;
if(dragStart){
const targets=[...dragRows];
dragStart=null;
const quote=targets.map(target=>target.textContent||'').join('\n').trim();
commentOnTargets(targets,[],quote);
clearSplitSelection();
return}
const selection=getSelection();
if(!selection.rangeCount||selection.isCollapsed)clearSplitSelection();
});
document.addEventListener('pointercancel',cancelPointerSelection);
addEventListener('blur',cancelPointerSelection);
$$('[data-view]').forEach(b=>b.onclick=()=>{
view=b.dataset.view;
$$('[data-view]').forEach(x=>x.classList.toggle('on',x===b));
render()}
);
new ResizeObserver(([entry])=>document.documentElement.style.setProperty('--review-header-height',`${entry.target.offsetHeight}px`)).observe(document.querySelector('.review>header'));
const send=verdict=>post({
verdict,note:$('#overall').value.trim(),comments:comments.map(({id,...comment})=>comment),viewed}
);
$('#approve').onclick=()=>send('approve');
$('#changes').onclick=()=>send('changes');
render();
"""
    )
    return page(f"map review: {task}", "review", head, body, footer, script)


@dataclass(frozen=True)
class PageSession:
    html: bytes
    feedback_path: Path
    viewed_path: Path | None = None

    def save(self, payload: dict[str, Any]) -> None:
        feedback = dict(payload)
        viewed = feedback.pop("viewed", None)
        if viewed is not None and self.viewed_path is not None:
            write_json(self.viewed_path, viewed)
        write_json(self.feedback_path, feedback)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")
    temporary.replace(path)


def handler_for(session: PageSession) -> type[BaseHTTPRequestHandler]:
    class PageHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/":
                self.reply(404, b"not found", "text/plain; charset=utf-8")
                return
            self.reply(200, session.html, "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if self.path != "/feedback":
                self.reply(404, b"not found", "text/plain; charset=utf-8")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise TypeError("feedback must be a json object")
                session.save(payload)
            except (
                json.JSONDecodeError,
                TypeError,
                UnicodeDecodeError,
                ValueError,
            ) as error:
                self.reply(400, str(error).encode(), "text/plain; charset=utf-8")
                return
            self.reply(200, b"ok", "text/plain; charset=utf-8")
            self.server.done = True

        def reply(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            return

    return PageHandler


class PageServer(HTTPServer):
    done = False


def create_server(session: PageSession) -> PageServer:
    return PageServer(("127.0.0.1", 0), handler_for(session))


def serve(html: str, feedback_path: Path, viewed_path: Path | None = None) -> None:
    session = PageSession(html.encode(), feedback_path, viewed_path)
    with create_server(session) as server:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        print(f"serving {url}", flush=True)
        webbrowser.open(url)
        while not server.done:
            server.handle_request()
    print(f"feedback written to {feedback_path}")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("proposals", "review"):
        sys.exit("usage: pages.py proposals|review <run_dir>")
    mode, run_dir = sys.argv[1], Path(sys.argv[2]).expanduser()
    if mode == "proposals":
        data: dict = json.loads((run_dir / "proposals.json").read_text(encoding="utf-8"))
        serve(render_proposals(data), run_dir / "feedback.json")
    else:
        patch = (run_dir / "diff.patch").read_text(encoding="utf-8", errors="replace")
        replies_path = run_dir / "replies.json"
        summary_path = run_dir / "summary.json"
        viewed_path = run_dir / "viewed.json"
        replies = json.loads(replies_path.read_text(encoding="utf-8")) if replies_path.exists() else []
        summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else []
        files = parse_diff(patch)
        files.sort(key=lambda item: tree_order(item["path"]))
        for item in files:
            rows = json.dumps(item["rows"], sort_keys=True).encode()
            item["hash"] = hashlib.sha1(rows).hexdigest()
        add_context(files)
        viewed = json.loads(viewed_path.read_text(encoding="utf-8")) if viewed_path.exists() else {}
        serve(
            render_review(run_dir.name, files, replies, summary, viewed),
            run_dir / "review-feedback.json",
            viewed_path,
        )


if __name__ == "__main__":
    main()
