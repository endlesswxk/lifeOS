# -*- coding: utf-8 -*-
"""从 cards.json 生成单文件检索站：site/index.html

单文件、无依赖、离线可用、可直接丢到 GitHub Pages / Cloudflare Pages。
内容全部内嵌进 HTML，双击即用；改 cards.json 后重跑本脚本即可。

    python 数据与脚本/build_site.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
SITE = PKG / "site"

DATA = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
META = DATA["meta"]
CARDS = DATA["cards"]

LEVELS = [
    ("L0", "一票否决"), ("L1", "每天"), ("L2", "每周"), ("L3", "每年/按年龄"),
    ("L4", "出事那一刻"), ("L5", "一次性办完"), ("L6", "情绪与心理"), ("DONT", "省钱的别做"),
]

# 只把检索与渲染需要的字段塞进页面，避免体积过大
PAYLOAD = {
    "meta": {
        "title": META["title"],
        "version": META["version"],
        "built_at": META["built_at"],
        "sources": META["sources"],
        "note": META["note"],
    },
    "levels": LEVELS,
    "cards": [
        {
            "id": c["id"], "lv": c["level"], "sec": c["section"], "t": c["title"],
            "do": c["do"], "harm": c["harm"], "ev": c["evidence"], "g": c["grade"],
            "src": c["source"], "pit": c.get("pitfalls", []), "nf": c.get("notFor", ""),
            "kw": c["keywords"], "rel": c.get("related", []),
        }
        for c in CARDS
    ],
}

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="description" content="个人健康知识库 __COUNT__ 张卡：怎么做、不做的后果、证据与出处。离线可用。">
<title>个人健康知识库 · __COUNT__ 张卡</title>
<style>
  :root{
    --bg:#f7f7f5; --fg:#1c1c1e; --muted:#6b6b70; --line:#e3e3df; --card:#ffffff;
    --accent:#2e7d8f; --warn:#b23b3b; --ok:#2f7d4f; --chip:#eef1f0;
    --a:#1f6f43; --b:#2e7d8f; --c:#8a6d1f; --d:#8a4b1f; --n:#6b6b70;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#131416; --fg:#e9e9ea; --muted:#9a9aa0; --line:#2a2c30; --card:#1b1d20;
           --accent:#63b7c8; --warn:#e07a7a; --ok:#6cc38d; --chip:#23262a; }
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--fg)}
  body{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
       -webkit-text-size-adjust:100%; padding-bottom:4rem}
  header{padding:2rem 1.25rem 1rem;max-width:900px;margin:0 auto}
  h1{font-size:1.5rem;margin:0 0 .35rem;letter-spacing:.01em}
  .sub{color:var(--muted);font-size:.9rem;margin:0}
  .controls{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 92%,transparent);
            backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:.75rem 1.25rem}
  .controls-inner{max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:.6rem}
  .searchbox{display:flex;gap:.5rem;align-items:center}
  input[type=search]{flex:1;font:inherit;font-size:1rem;padding:.7rem .9rem;border-radius:.7rem;
    border:1px solid var(--line);background:var(--card);color:var(--fg);min-width:0}
  input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px}
  .chips{display:flex;gap:.4rem;overflow-x:auto;padding-bottom:.15rem;scrollbar-width:none}
  .chips::-webkit-scrollbar{display:none}
  .chip{white-space:nowrap;font-size:.82rem;padding:.35rem .7rem;border-radius:999px;
        border:1px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer;font-family:inherit}
  .chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
  .row2{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;font-size:.82rem;color:var(--muted)}
  select{font:inherit;font-size:.82rem;padding:.3rem .5rem;border-radius:.5rem;border:1px solid var(--line);
         background:var(--card);color:var(--fg)}
  .ghost{font:inherit;font-size:.82rem;padding:.3rem .6rem;border-radius:.5rem;border:1px solid var(--line);
         background:var(--card);color:var(--muted);cursor:pointer}
  main{max-width:900px;margin:0 auto;padding:1rem 1.25rem}
  .hit{color:var(--muted);font-size:.85rem;margin:.2rem 0 1rem}
  .card{background:var(--card);border:1px solid var(--line);border-radius:.9rem;padding:1rem 1.1rem;margin:0 0 .85rem}
  .card h2{font-size:1.02rem;margin:0 0 .5rem;line-height:1.45;font-weight:650}
  .badges{display:flex;gap:.35rem;flex-wrap:wrap;margin:0 0 .55rem}
  .badge{font-size:.72rem;padding:.15rem .45rem;border-radius:.35rem;background:var(--chip);color:var(--muted)}
  .badge.g{font-weight:700}
  .badge.g-A{color:var(--a)} .badge.g-B{color:var(--b)} .badge.g-C{color:var(--c)}
  .badge.g-D{color:var(--d)} .badge.g-N{color:var(--n)}
  .harm{font-size:.94rem;margin:0 0 .6rem;padding-left:.7rem;border-left:3px solid var(--warn);color:var(--fg)}
  .harm span{color:var(--muted);font-size:.8rem;display:block;margin-bottom:.15rem}
  details{border-top:1px dashed var(--line);padding-top:.55rem;margin-top:.35rem}
  summary{cursor:pointer;font-size:.86rem;color:var(--accent);list-style:none}
  summary::-webkit-details-marker{display:none}
  summary::before{content:"▸ ";}
  details[open] summary::before{content:"▾ ";}
  .body{margin:.6rem 0 0;font-size:.9rem}
  .body h3{font-size:.8rem;color:var(--muted);margin:.9rem 0 .25rem;font-weight:600;letter-spacing:.03em}
  .body ol,.body ul{margin:.2rem 0;padding-left:1.15rem}
  .body li{margin:.18rem 0}
  .body p{margin:.2rem 0}
  .kw{display:flex;gap:.3rem;flex-wrap:wrap}
  .kw span{font-size:.72rem;background:var(--chip);color:var(--muted);padding:.1rem .4rem;border-radius:.3rem}
  a{color:var(--accent)}
  footer{max-width:900px;margin:2rem auto 0;padding:1.25rem;border-top:1px solid var(--line);
         color:var(--muted);font-size:.8rem}
  footer p{margin:.35rem 0}
  mark{background:color-mix(in srgb,var(--accent) 28%,transparent);color:inherit;border-radius:.2rem;padding:0 .1rem}
  .empty{color:var(--muted);text-align:center;padding:3rem 0}
  .back{display:inline-block;font-size:.82rem;color:var(--muted);text-decoration:none;
        border:1px solid var(--line);border-radius:999px;padding:.25rem .7rem;margin-bottom:.6rem}
  .back:hover{color:var(--accent);border-color:var(--accent)}
  .card.focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 22%,transparent)}
  .card.focus h2{color:var(--accent)}
  @media print{
    .controls,footer{display:none} body{background:#fff;color:#000;padding:0}
    .card{break-inside:avoid;border-color:#ccc;margin-bottom:.4rem;padding:.5rem}
    main{max-width:none;padding:0} details{display:block}
    details>.body{display:block !important}
  }
</style>
</head>
<body>
<header>
  <a class="back" id="back" href="../../" hidden>← 生活系统</a>
  <h1>个人健康知识库</h1>
  <p class="sub">__COUNT__ 张卡 · 每条含「怎么做 / 不做的后果 / 证据与出处」 · 版本 __VERSION__（__BUILT__）</p>
</header>

<div class="controls">
  <div class="controls-inner">
    <div class="searchbox">
      <input id="q" type="search" placeholder="搜症状或动作：打鼾 / 胸口疼 / 睡不着 / 疫苗…" autocomplete="off" aria-label="检索">
    </div>
    <div class="chips" id="lvs" role="group" aria-label="按层级筛选"></div>
    <div class="row2">
      <label>证据
        <select id="g">
          <option value="">全部</option>
          <option value="A">A 强</option><option value="B">B 队列</option>
          <option value="C">C 弱</option><option value="D">D 无直接证据</option>
          <option value="-">- 常识</option>
        </select>
      </label>
      <button class="ghost" id="expand">全部展开</button>
      <span id="count"></span>
    </div>
  </div>
</div>

<main>
  <p class="hit" id="hit"></p>
  <div id="list"></div>
</main>

<footer>
  <p><strong>边界</strong>：证据分级 A/B/C/D 沿用 HowToLiveLonger 的实用分级，不是 GRADE；
  HR/RR/OR 是人群关联，不能相乘，也不能换算成个人寿命。危害一栏有一部分是通用医学常识
  （急救时间窗、中毒机制），出处栏标的是「行动」本身的来源。</p>
  <p><strong>不能替代医生</strong>：出事那一刻（L4）是现场处置，不是诊断；急症按卡上写的打 120 / 去急诊。</p>
  <p><strong>来源</strong>：HowToLiveLonger（Unlicense）· HumanSystemOptimization（无许可证，仅事实引用与改写）·
  HowToLiveBetter（CC BY 4.0）· HowToCook（Unlicense）。完整引用见仓库内 <code>02-引用与来源.md</code>。</p>
  <p>单文件离线可用 · 无网络请求 · 无追踪 · 数据全部内嵌在本页</p>
</footer>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('data').textContent);
  var cards = D.cards, levels = D.levels;
  var byId = {}; cards.forEach(function(c){ byId[c.id] = c; });
  var lvName = {}; levels.forEach(function(p){ lvName[p[0]] = p[1]; });

  var qEl = document.getElementById('q'),
      gEl = document.getElementById('g'),
      lvEl = document.getElementById('lvs'),
      listEl = document.getElementById('list'),
      hitEl = document.getElementById('hit'),
      countEl = document.getElementById('count'),
      expBtn = document.getElementById('expand');

  var state = { q:"", lv:"", g:"" };

  // 层级筛选 chips
  var all = document.createElement('button');
  all.className = 'chip'; all.textContent = '全部'; all.dataset.lv = '';
  all.setAttribute('aria-pressed','true'); lvEl.appendChild(all);
  levels.forEach(function(p){
    var b = document.createElement('button');
    b.className = 'chip'; b.dataset.lv = p[0];
    b.textContent = p[0] + ' ' + p[1];
    b.setAttribute('aria-pressed','false');
    lvEl.appendChild(b);
  });
  lvEl.addEventListener('click', function(e){
    var b = e.target.closest('.chip'); if(!b) return;
    state.lv = b.dataset.lv;
    Array.prototype.forEach.call(lvEl.children, function(c){
      c.setAttribute('aria-pressed', String(c.dataset.lv === state.lv));
    });
    render();
  });

  function hay(c){
    return [c.t, c.sec, c.harm, c.ev, c.src, c.nf, c.do.join(' '), c.pit.join(' '), c.kw.join(' ')].join(' ').toLowerCase();
  }
  cards.forEach(function(c){ c._hay = hay(c); c._kw = c.kw.join('|').toLowerCase(); });

  function score(c, terms){
    var s = 0, t = c.t.toLowerCase(), hit = 0;
    for (var i=0;i<terms.length;i++){
      var term = terms[i], st = 0;
      if (c._kw.indexOf(term) >= 0) st += 5;
      if (t.indexOf(term) >= 0) st += 3;
      if (c._hay.indexOf(term) >= 0) st += 1;
      if (st) hit++;
      s += st;
    }
    return hit === terms.length ? s : 0;  // 多词按「与」：都要命中
  }

  function esc(s){
    return String(s).replace(/[&<>"]/g, function(ch){
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[ch];
    });
  }
  function mark(s, terms){
    var out = esc(s);
    terms.forEach(function(t){
      if(!t) return;
      try {
        out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&') + ')','gi'), '<mark>$1</mark>');
      } catch(e){}
    });
    return out;
  }

  function cardHTML(c, terms){
    var g = c.g === '-' ? 'N' : c.g;
    var h = '';
    h += '<article class="card" id="c-' + c.id + '">';
    h += '<div class="badges">'
       + '<span class="badge">' + esc(c.lv) + ' ' + esc(lvName[c.lv] || '') + '</span>'
       + '<span class="badge g g-' + g + '" title="证据等级 ' + esc(c.g) + '">证据 ' + esc(c.g) + '</span>'
       + '</div>';
    h += '<h2>' + mark(c.t, terms) + '</h2>';
    h += '<p class="harm"><span>不做的后果</span>' + mark(c.harm, terms) + '</p>';
    h += '<details><summary>怎么做、证据、误区</summary><div class="body">';
    h += '<h3>怎么做</h3><ol>' + c.do.map(function(x){ return '<li>' + mark(x, terms) + '</li>'; }).join('') + '</ol>';
    h += '<h3>证据</h3><p>' + mark(c.ev, terms) + '</p>';
    h += '<h3>出处</h3><p>' + esc(c.src) + '</p>';
    if (c.pit && c.pit.length){
      h += '<h3>常见误区</h3><ul>' + c.pit.map(function(x){ return '<li>' + mark(x, terms) + '</li>'; }).join('') + '</ul>';
    }
    if (c.nf){ h += '<h3>不适用 / 先问医生</h3><p>' + mark(c.nf, terms) + '</p>'; }
    if (c.rel && c.rel.length){
      h += '<h3>关联</h3><p>' + c.rel.map(function(id){
        return byId[id] ? '<a href="#c-' + id + '">' + esc(byId[id].t) + '</a>' : esc(id);
      }).join(' · ') + '</p>';
    }
    h += '<h3>检索词</h3><div class="kw">' + c.kw.map(function(k){ return '<span>' + esc(k) + '</span>'; }).join('') + '</div>';
    h += '</div></details></article>';
    return h;
  }

  function render(){
    var terms = state.q.trim().toLowerCase().split(/\\s+/).filter(Boolean);
    var rows = cards.filter(function(c){
      if (state.lv && c.lv !== state.lv) return false;
      if (state.g && c.g !== state.g) return false;
      return true;
    });
    if (terms.length){
      rows = rows.map(function(c){ return { c:c, s:score(c, terms) }; })
                 .filter(function(x){ return x.s > 0; })
                 .sort(function(a,b){ return b.s - a.s || a.c.t.length - b.c.t.length; })
                 .map(function(x){ return x.c; });
    }
    countEl.textContent = '共 ' + rows.length + ' 张';
    hitEl.textContent = terms.length
      ? '检索「' + state.q.trim() + '」命中 ' + rows.length + ' 张（多词需同时命中）'
      : '';
    if (!rows.length){
      listEl.innerHTML = '<p class="empty">没有命中。试试更口语的词：打呼噜、胸口疼、睡不着、拉肚子……</p>';
      return;
    }
    listEl.innerHTML = rows.map(function(c){ return cardHTML(c, terms); }).join('');
  }

  var t = null;
  qEl.addEventListener('input', function(){
    clearTimeout(t);
    t = setTimeout(function(){ state.q = qEl.value; render(); }, 120);
  });
  gEl.addEventListener('change', function(){ state.g = gEl.value; render(); });
  expBtn.addEventListener('click', function(){
    var open = expBtn.dataset.open === '1';
    Array.prototype.forEach.call(listEl.querySelectorAll('details'), function(d){ d.open = !open; });
    expBtn.dataset.open = open ? '0' : '1';
    expBtn.textContent = open ? '全部展开' : '全部收起';
  });
  document.addEventListener('keydown', function(e){
    if (e.key === '/' && document.activeElement !== qEl){ e.preventDefault(); qEl.focus(); }
  });

  // ---- 深链：#c-<卡 id> 直接定位、展开、高亮（lifeOS 的「依据 ↗」走这里）
  function openHash(){
    var m = /^#c-([A-Za-z0-9_.-]+)$/.exec(location.hash || '');
    if (!m) return;
    var el = document.getElementById('c-' + m[1]);
    if (!el) {  // 被层级/证据筛选挡住了，就按 id 搜出来
      state.q = m[1]; state.lv = ''; state.g = ''; qEl.value = m[1];
      Array.prototype.forEach.call(lvEl.children, function(c){
        c.setAttribute('aria-pressed', String(!c.dataset.lv));
      });
      gEl.value = '';
      render();
      el = document.getElementById('c-' + m[1]);
      if (!el) return;
    }
    var d = el.querySelector('details'); if (d) d.open = true;
    Array.prototype.forEach.call(document.querySelectorAll('.card.focus'), function(x){ x.classList.remove('focus'); });
    el.classList.add('focus');
    setTimeout(function(){ el.scrollIntoView({ block: 'start' }); }, 30);
  }
  window.addEventListener('hashchange', openHash);

  // ---- 从 app 进来时显示「返回生活系统」
  (function(){
    var b = document.getElementById('back');
    var httpish = location.protocol === 'http:' || location.protocol === 'https:';
    if (b && httpish && /\\/kb\\/site\\/?$/.test(location.pathname)) b.hidden = false;
  })();

  render();
  openHash();
})();
</script>
</body>
</html>
"""


def build():
    SITE.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(PAYLOAD, ensure_ascii=False, separators=(",", ":"))
    html = (
        HTML.replace("__DATA__", payload)
        .replace("__COUNT__", str(len(CARDS)))
        .replace("__VERSION__", META["version"])
        .replace("__BUILT__", META["built_at"])
    )
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"site -> {out}  ({out.stat().st_size:,} B)  cards={len(CARDS)}")


if __name__ == "__main__":
    build()
