from pathlib import Path
import html
import json


ROOT = Path(".")
GT = ROOT / "my_30"
RESULTS = ROOT / "results"
OUT = ROOT / "gallery.html"
AUTOFIGURE = ROOT / "autofigure-edit" / "batch"
BENCHMARK_GT = Path(r"D:\project\ppt-agent\PaperBanana\diagram\benchmark\my_30")
DIFF_DIRS = {
    "simple": Path(r"D:\project\ppt-agent\PaperBanana\diagram\benchmark\simple"),
    "medium": Path(r"D:\project\ppt-agent\PaperBanana\diagram\benchmark\medium"),
    "hard": Path(r"D:\project\ppt-agent\PaperBanana\diagram\benchmark\hard"),
}
DIFF_ORDER = {"simple": 0, "medium": 1, "hard": 2, "unknown": 3}

SVG_COLS = [
    ("template", "template.svg"),
    ("filled", "filled.svg"),
]


def rel(p):
    return p.as_posix()


rows = []
sources = {}
difficulty_by_name = {}
for difficulty, folder in DIFF_DIRS.items():
    if folder.exists():
        for p in folder.iterdir():
            if p.is_file():
                difficulty_by_name[p.name] = difficulty

id_to_original = {}
if BENCHMARK_GT.exists():
    originals = sorted(
        p for p in BENCHMARK_GT.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    id_to_original = {f"{i:04d}": p.name for i, p in enumerate(originals, 1)}

ids = sorted(p.name for p in RESULTS.iterdir() if p.is_dir() and p.name.isdigit())
for case_id in ids:
    gt = next(iter(sorted(GT.glob(f"{case_id}.*"))), None)
    result_dir = RESULTS / case_id
    original_name = id_to_original.get(case_id, "")
    difficulty = difficulty_by_name.get(original_name, "unknown")

    row = {"id": case_id, "difficulty": difficulty, "gt": rel(gt) if gt else ""}
    for key, name in SVG_COLS:
        path = result_dir / name
        row[key] = rel(path) if path.exists() else ""
        if path.exists():
            sources[rel(path)] = path.read_text(encoding="utf-8", errors="replace")
    gpt55 = ROOT / "gpt_5_5" / case_id / "input.svg"
    row["gpt55"] = rel(gpt55) if gpt55.exists() else ""
    if gpt55.exists():
        sources[rel(gpt55)] = gpt55.read_text(encoding="utf-8", errors="replace")
    autofigure = AUTOFIGURE / case_id / "final.svg"
    row["autofigure"] = rel(autofigure) if autofigure.exists() else ""
    if autofigure.exists():
        sources[rel(autofigure)] = autofigure.read_text(encoding="utf-8", errors="replace")
    rows.append(row)

rows.sort(key=lambda r: (DIFF_ORDER.get(r["difficulty"], 9), r["id"]))


html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GT / SVG Gallery</title>
<style>
body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #111; }}
header {{ position: sticky; top: 0; z-index: 2; padding: 12px 18px; background: #fff; border-bottom: 1px solid #ddd; }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; background: #fff; }}
th {{ position: sticky; top: 49px; z-index: 1; background: #f0f2f5; text-align: left; }}
.id {{ width: 64px; font-weight: 700; }}
.difficulty {{ width: 78px; font-weight: 700; }}
.group td {{ position: sticky; top: 81px; z-index: 1; background: #e8edf5; font-weight: 700; padding: 10px; }}
.cell {{ height: 555px; display: grid; grid-template-rows: 525px 24px; gap: 4px; }}
.preview {{ width: 100%; height: 525px; border: 1px solid #ccc; background: white; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.preview img, .preview object {{ width: 100%; height: 100%; object-fit: contain; object-position: center center; display: block; border: 0; }}
.actions {{ height: 24px; display: flex; align-items: center; justify-content: center; }}
button {{ cursor: pointer; padding: 2px 10px; height: 22px; border: 1px solid #aaa; background: #fff; font-size: 12px; line-height: 16px; }}
.missing {{ color: #999; height: 100%; display: flex; align-items: center; justify-content: center; }}
#modal {{ display: none; position: fixed; inset: 0; z-index: 9; background: rgba(0,0,0,.55); }}
#panel {{ position: absolute; inset: 24px; background: #fff; display: flex; flex-direction: column; }}
#bar {{ padding: 10px; border-bottom: 1px solid #ddd; display: flex; gap: 8px; align-items: center; }}
#title {{ flex: 1; font-weight: 700; }}
pre {{ margin: 0; padding: 14px; overflow: auto; flex: 1; background: #111; color: #eee; font-size: 13px; line-height: 1.45; }}
.tag {{ color: #7dd3fc; }}
.attr {{ color: #facc15; }}
.value {{ color: #86efac; }}
.comment {{ color: #94a3b8; }}
</style>
</head>
<body>
<header>GT / template / template_filled / gpt5.5 direct / autofigure edit</header>
<table>
<thead>
<tr><th class="id">ID</th><th class="difficulty">&#38590;&#24230;</th><th>GT</th><th>template</th><th>template_filled</th><th>gpt5.5 direct</th><th>autofigure edit</th></tr>
</thead>
<tbody id="tbody"></tbody>
</table>

<div id="modal">
  <div id="panel">
    <div id="bar"><span id="title"></span><button onclick="copyCode()">&#22797;&#21046;</button><button onclick="closeCode()">&#20851;&#38381;</button></div>
    <pre id="code"></pre>
  </div>
</div>

<script>
const rows = {json.dumps(rows, ensure_ascii=False)};
const sources = {json.dumps(sources, ensure_ascii=False)};

function preview(path, isSvg) {{
  if (!path) return '<div class="missing">missing</div>';
  const tag = isSvg ? `<object data="${{path}}" type="image/svg+xml"></object>` : `<img src="${{path}}">`;
  const btn = isSvg ? `<button onclick="openCode('${{path}}')">&#28304;&#30721;</button>` : '';
  return `<div class="cell"><div class="preview">${{tag}}</div><div class="actions">${{btn}}</div></div>`;
}}

let lastDifficulty = '';
document.getElementById('tbody').innerHTML = rows.map(r => {{
  const group = r.difficulty !== lastDifficulty
    ? `<tr class="group"><td colspan="7">${{r.difficulty}}</td></tr>`
    : '';
  lastDifficulty = r.difficulty;
  return group + `
    <tr>
      <td class="id">${{r.id}}</td>
      <td class="difficulty">${{r.difficulty}}</td>
      <td>${{preview(r.gt, false)}}</td>
      <td>${{preview(r.template, true)}}</td>
      <td>${{preview(r.filled, true)}}</td>
      <td>${{preview(r.gpt55, true)}}</td>
      <td>${{preview(r.autofigure, true)}}</td>
    </tr>
  `;
}}).join('');

function openCode(path) {{
  const src = sources[path] || '';
  document.getElementById('title').textContent = path;
  document.getElementById('code').innerHTML = highlightSvg(src);
  document.getElementById('modal').style.display = 'block';
}}

function closeCode() {{
  document.getElementById('modal').style.display = 'none';
}}

function copyCode() {{
  navigator.clipboard.writeText(document.getElementById('code').textContent);
}}

function esc(s) {{
  return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}}

function highlightSvg(src) {{
  return esc(src)
    .replace(/(&lt;!--[\\s\\S]*?--&gt;)/g, '<span class="comment">$1</span>')
    .replace(/(&lt;\\/?)([\\w:.-]+)/g, '$1<span class="tag">$2</span>')
    .replace(/(\\s)([\\w:.-]+)(=)("[^"]*"|'[^']*')/g, '$1<span class="attr">$2</span>$3<span class="value">$4</span>');
}}

document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeCode();
}});
</script>
</body>
</html>
"""

OUT.write_text(html_text, encoding="utf-8")
print(f"wrote {OUT}")

