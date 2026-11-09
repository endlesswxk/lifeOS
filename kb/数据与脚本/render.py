# -*- coding: utf-8 -*-
"""Render 个人健康检查清单 from checklist.json into Markdown + printable A4 HTML."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "checklist.json").read_text(encoding="utf-8"))
OUT_DIR = ROOT.parent / "一页纸清单"
OUT_MD = OUT_DIR / "个人健康检查清单.md"
OUT_HTML = OUT_DIR / "个人健康检查清单.html"

GRADE_CLASS = {"A": "g-a", "B": "g-b", "C": "g-c", "D": "g-d", "-": "g-n"}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def brief(s: str) -> str:
    """Printed page keeps only the leading clause; the .md file keeps the full text."""
    cut = s.split("（")[0].strip()
    return cut if len(cut) >= 8 else s.strip()


# ---------------------------------------------------------------- Markdown
def render_md() -> str:
    L = []
    L.append(f"# {DATA['title']}")
    L.append("")
    L.append(f"> {DATA['subtitle']}")
    L.append(">")
    L.append(f"> **怎么用**：{DATA['principle']}")
    L.append("")
    total = 0
    for sec in DATA["sections"]:
        L.append(f"## {sec['level']} · {sec['title']}")
        L.append("")
        if sec.get("note"):
            L.append(f"*{sec['note']}*")
            L.append("")
        for it in sec["items"]:
            total += 1
            g = f"[{it['g']}] " if it["g"] != "-" else ""
            std = f"（{it['std']}）" if it["std"] else ""
            L.append(f"- [ ] {it['t']}{std} {g}— {it['s']}".replace("  ", " "))
            L.append(f"  - **{sec.get('harmLabel', '后果')}**：{it['harm']}")
        L.append("")
    d = DATA["donts"]
    L.append(f"## {d['title']}")
    L.append("")
    if d.get("note"):
        L.append(f"*{d['note']}*")
        L.append("")
    for it in d["items"]:
        g = f"[{it['g']}] " if it["g"] != "-" else ""
        L.append(f"- [ ] {it['t']} {g}— {it['s']}".replace("  ", " "))
        L.append(f"  - **{d.get('harmLabel', '做了会怎样')}**：{it['harm']}")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"**读数字的前置说明**：{DATA['caveat']}")
    L.append("")
    L.append("**证据分级**：" + "；".join(f"`{x['k']}` {x['v']}" for x in DATA["legend"]))
    L.append("")
    L.append("**来源**：")
    for s in DATA["sources"]:
        L.append(f"- `{s['k']}` {s['v']}")
    L.append("")
    L.append(f"**范围说明**：{DATA['out_of_scope']}")
    L.append("")
    L.append(f"共 {total} 条行动 + {len(d['items'])} 条别做 = {total + len(d['items'])} 条；每条都标了不做的后果（别做一节标的是做了会怎样）。")
    L.append("")
    return "\n".join(L)


CSS = """
@page { size: A4; margin: 6mm 7mm 5mm; }
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:#fff;color:#1b1b1f;
  font:7.3pt/1.3 "Microsoft YaHei","PingFang SC","Segoe UI",system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:196mm;margin:0 auto;padding:0}
header.hd{display:flex;align-items:flex-end;gap:8px;border-bottom:1.4pt solid #1b1b1f;padding-bottom:2px;margin-bottom:3px}
header.hd h1{font-size:13pt;margin:0;letter-spacing:-.2px;font-weight:700}
header.hd .sub{font-size:7pt;color:#666;padding-bottom:1.5px}
.principle{font-size:7pt;color:#444;background:#f4f5f7;border-left:2pt solid #3a5ccc;padding:2px 6px;margin:0 0 4px}
.cols{column-count:2;column-gap:5mm}
section.sec{break-inside:avoid;margin-bottom:2px}
section.sec h2{margin-top:0;
  font-size:8.4pt;margin:0 0 1px;font-weight:700;display:flex;align-items:baseline;gap:4px;
  border-bottom:.7pt solid #c9cace;padding-bottom:1px;
}
section.sec h2 .lv{
  font-size:6.2pt;font-weight:700;background:#1b1b1f;color:#fff;border-radius:2.5px;
  padding:.4px 3px;letter-spacing:.3px;flex:none;
}
section.sec h2 .snote{font-size:6.4pt;font-weight:400;color:#8a8c95;flex:1;text-align:right}
label.it{display:flex;gap:3px;align-items:flex-start;padding:.05px 0;break-inside:avoid}
label.it input{
  flex:none;appearance:none;-webkit-appearance:none;width:6.8px;height:6.8px;margin:1.9px 0 0;
  border:.8pt solid #6b6d75;border-radius:1.4px;background:#fff;cursor:pointer;position:relative;
}
label.it input:checked{background:#18794e;border-color:#18794e}
label.it input:checked::after{
  content:"";position:absolute;left:1.3px;top:-.6px;width:2.4px;height:4.6px;
  border:solid #fff;border-width:0 1.3px 1.3px 0;transform:rotate(42deg);
}
label.it .tx{flex:1;min-width:0}
label.it .std{color:#7a7c85}
label.it .src{color:#a3a5ae;font-size:6pt}
label.it .harm{color:#9c2b2b}
label.it .harm .hl{
  font-size:5.7pt;background:#f7dfe0;color:#9c2b2b;border-radius:2px;padding:0 2px;margin-right:2px;
  font-weight:700;vertical-align:.4px;
}
label.it input:checked + .tx{color:#a9abb3}
label.it input:checked + .tx .harm{color:#c39a9a}
.g{font-size:5.8pt;font-weight:700;border-radius:2px;padding:0 2px;margin-left:1px;vertical-align:.5px}
.g-a{background:#d7f2e3;color:#0d5c37}
.g-b{background:#dce6fb;color:#1f3d8f}
.g-c{background:#f6ebcf;color:#7a5313}
.g-d{background:#fadadd;color:#8d1c24}
.g-n{background:#ececef;color:#666}
.donts{break-inside:avoid;margin-top:3px;border:.6pt solid #d9dade;border-radius:3px;padding:2px 5px 3px;background:#fbfaf7}
.donts h2{font-size:8pt;margin:0 0 1px;font-weight:700;display:flex;gap:4px;align-items:baseline}
.donts h2 .snote{font-size:6.4pt;font-weight:400;color:#8a8c95}
.donts .grid{column-count:2;column-gap:5mm}
.donts label.it{padding:.1px 0}
footer{margin-top:2px;border-top:.6pt solid #d7d8dc;padding-top:1.5px;font-size:5.9pt;color:#6b6d75;line-height:1.36}
footer b{color:#1b1b1f}
footer .lg{margin:1px 0}
footer .sc span{white-space:nowrap;margin-right:6px}
.bar{
  position:sticky;top:0;z-index:9;background:#1b1b1f;color:#fff;font-size:8pt;
  display:flex;align-items:center;gap:10px;padding:3px 8px;border-radius:3px;margin-bottom:4px;
}
.bar .p{flex:1}
.bar button{font:inherit;background:#3a3a42;color:#fff;border:0;border-radius:3px;padding:1.5px 7px;cursor:pointer}
.bar button:hover{background:#4a4a55}
@media print{
  .bar{display:none}
  body{font-size:7.25pt}
}
"""

JS = """
(function(){
  var KEY='health-checklist-v1';
  var boxes=[].slice.call(document.querySelectorAll('input[type=checkbox]'));
  var state={};
  try{state=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){state={}}
  boxes.forEach(function(b){
    if(state[b.dataset.id]) b.checked=true;
    b.addEventListener('change',function(){
      state[b.dataset.id]=b.checked;
      try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}
      update();
    });
  });
  function update(){
    var n=boxes.filter(function(b){return b.checked}).length;
    document.getElementById('prog-done').textContent='已做到 '+n+' / '+boxes.length+'（'+Math.round(n/boxes.length*100)+'%）';
  }
  document.getElementById('btn-reset').addEventListener('click',function(){
    boxes.forEach(function(b){b.checked=false});
    state={};try{localStorage.removeItem(KEY)}catch(e){}
    update();
  });
  document.getElementById('btn-print').addEventListener('click',function(){window.print()});
  update();
})();
"""


def item_html(it, cid, harm_label):
    p = []
    p.append('<label class="it"><input type="checkbox" data-id="' + cid + '"><span class="tx">')
    p.append(esc(it["t"]))
    if it["g"] != "-":
        p.append('<span class="g %s">%s</span>' % (GRADE_CLASS[it["g"]], esc(it["g"])))
    if it.get("std"):
        p.append('<span class="std">（' + esc(it["std"]) + '）</span>')
    p.append('<span class="harm"><span class="hl">' + esc(harm_label) + '</span>' + esc(it["harm"]) + '</span>')
    p.append('<span class="src">· ' + esc(it["s"]) + '</span>')
    p.append('</span></label>')
    return "".join(p)


def render_html() -> str:
    parts = []
    parts.append('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">')
    parts.append('<title>' + esc(DATA["title"]) + '</title>')
    parts.append('<style>' + CSS + '</style></head><body>')
    parts.append('<div class="bar"><div class="p" id="prog-done">已做到 0 / 0</div>'
                 '<button id="btn-print" type="button">打印 / 存 PDF</button>'
                 '<button id="btn-reset" type="button">清空勾选</button></div>')
    parts.append('<div class="wrap">')
    parts.append('<header class="hd"><h1>' + esc(DATA["title"]) + '</h1>'
                 '<div class="sub">' + esc(DATA["subtitle"]) + '</div></header>')
    parts.append('<p class="principle">' + esc(DATA["principle"]) + '</p>')
    parts.append('<div class="cols">')

    n = 0
    for sec in DATA["sections"]:
        hl = sec.get("harmLabel", "后果")
        parts.append('<section class="sec">')
        parts.append('<h2><span class="lv">' + esc(sec["level"]) + '</span>' + esc(sec["title"]))
        if sec.get("note"):
            parts.append('<span class="snote">' + esc(sec["note"]) + '</span>')
        parts.append('</h2>')
        for it in sec["items"]:
            n += 1
            parts.append(item_html(it, "%s-%02d" % (sec["id"], n), hl))
        parts.append('</section>')

    parts.append('</div>')

    d = DATA["donts"]
    hl = d.get("harmLabel", "做了会怎样")
    parts.append('<div class="donts"><h2>' + esc(d["title"]))
    if d.get("note"):
        parts.append('<span class="snote">' + esc(d["note"]) + '</span>')
    parts.append('</h2><div class="grid">')
    for it in d["items"]:
        n += 1
        parts.append(item_html(it, "dont-%02d" % n, hl))
    parts.append('</div></div>')

    parts.append('<footer>')
    parts.append('<div><b>读数字的前置说明：</b>' + esc(DATA["caveat"]) + '</div>')
    parts.append('<div class="lg"><b>证据分级：</b>' + ' · '.join(
        '<span class="g %s">%s</span> %s' % (GRADE_CLASS[x["k"]], esc(x["k"]), esc(x["v"])) for x in DATA["legend"]
    ) + '</div>')
    parts.append('<div class="sc"><b>来源：</b>' + ''.join(
        '<span><b>%s</b> %s</span>' % (esc(s["k"]), esc(brief(s["v"]))) for s in DATA["sources"]
    ) + '</div>')
    parts.append('<div><b>范围：</b>' + esc(DATA["out_of_scope"]) + '</div>')
    parts.append('</footer>')
    parts.append('</div>')
    parts.append('<script>' + JS + '</script>')
    parts.append('</body></html>')
    return "".join(parts)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)   # 目录不入库，需要时现生成
    OUT_MD.write_text(render_md(), encoding="utf-8")
    OUT_HTML.write_text(render_html(), encoding="utf-8")
    total = sum(len(s["items"]) for s in DATA["sections"]) + len(DATA["donts"]["items"])
    print("MD   ->", OUT_MD)
    print("HTML ->", OUT_HTML)
    print("items:", total)

