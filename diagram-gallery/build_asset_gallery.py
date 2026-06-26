from pathlib import Path
import json


ROOT = Path(".")
GT = ROOT / "my_30"
RESULTS = ROOT / "results"
OUT = ROOT / "asset_gallery.html"


def rel(p):
    return p.as_posix()


def files(folder):
    if not folder.exists():
        return []
    return [
        rel(p) for p in sorted(folder.iterdir())
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]


rows = []
sources = {}

for result_dir in sorted(p for p in RESULTS.iterdir() if p.is_dir() and p.name.isdigit()):
    case_id = result_dir.name
    gt = next(iter(sorted(GT.glob(f"{case_id}.*"))), None)
    template = result_dir / "template.svg"
    snippets = result_dir / "svg_candidate_snippets.svg"
    filled = result_dir / "filled.svg"

    row = {
        "id": case_id,
        "gt": rel(gt) if gt else "",
        "template": rel(template) if template.exists() else "",
        "snippets": rel(snippets) if snippets.exists() else "",
        "crops": files(result_dir / "assets" / "raster_required"),
        "filled": rel(filled) if filled.exists() else "",
    }
    for p in [template, snippets, filled]:
        if p.exists():
            sources[rel(p)] = p.read_text(encoding="utf-8", errors="replace")
    rows.append(row)


html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Asset Gallery</title>
<style>
body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #111; }}
header {{ position: sticky; top: 0; z-index: 2; padding: 12px 18px; background: #fff; border-bottom: 1px solid #ddd; }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; background: #fff; }}
th {{ position: sticky; top: 49px; z-index: 1; background: #f0f2f5; text-align: left; }}
.id {{ width: 58px; font-weight: 700; }}
.cell {{ height: 420px; display: grid; grid-template-rows: 392px 24px; gap: 4px; }}
.preview {{ height: 392px; border: 1px solid #ccc; background: #fff; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.preview img, .preview object {{ width: 100%; height: 100%; object-fit: contain; border: 0; }}
.actions {{ height: 24px; display: flex; justify-content: center; align-items: center; }}
button {{ cursor: pointer; padding: 2px 10px; height: 22px; border: 1px solid #aaa; background: #fff; font-size: 12px; }}
.missing {{ color: #999; height: 100%; display: flex; align-items: center; justify-content: center; }}
.grid {{ height: 420px; overflow: auto; border: 1px solid #ccc; background: #fff; display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 8px; padding: 8px; align-content: start; }}
.thumb {{ border: 1px solid #ddd; background: #fafafa; min-height: 120px; display: flex; flex-direction: column; gap: 4px; }}
.thumb img {{ width: 100%; height: 92px; object-fit: contain; background: white; }}
.name {{ font-size: 11px; color: #444; word-break: break-all; padding: 0 4px 4px; }}
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
<header>GT / template.svg / svg icon / crop raster / filled.svg</header>
<table>
<thead>
<tr><th class="id">ID</th><th>GT</th><th>template.svg</th><th>svg icon</th><th>crop raster</th><th>filled.svg</th></tr>
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

function svgCell(path) {{
  if (!path) return '<div class="missing">missing</div>';
  return `<div class="cell"><div class="preview"><object data="${{path}}" type="image/svg+xml"></object></div><div class="actions"><button onclick="openCode('${{path}}')">&#28304;&#30721;</button></div></div>`;
}}

function imageCell(path) {{
  if (!path) return '<div class="missing">missing</div>';
  return `<div class="cell"><div class="preview"><img src="${{path}}"></div><div></div></div>`;
}}

function cropGrid(paths) {{
  if (!paths.length) return '<div class="missing">missing</div>';
  return `<div class="grid">${{paths.map(p => `<div class="thumb"><img src="${{p}}"><div class="name">${{p.split('/').slice(-2).join('/')}}</div></div>`).join('')}}</div>`;
}}

document.getElementById('tbody').innerHTML = rows.map(r => `
  <tr>
    <td class="id">${{r.id}}</td>
    <td>${{imageCell(r.gt)}}</td>
    <td>${{svgCell(r.template)}}</td>
    <td>${{svgCell(r.snippets)}}</td>
    <td>${{cropGrid(r.crops)}}</td>
    <td>${{svgCell(r.filled)}}</td>
  </tr>
`).join('');

function openCode(path) {{
  document.getElementById('title').textContent = path;
  document.getElementById('code').innerHTML = highlightSvg(sources[path] || '');
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

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT}")
