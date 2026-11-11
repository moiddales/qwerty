import re, sys, html
import markdown

src, out_html = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()

# protect fenced code first
codes = []
def keep_code(m):
    codes.append(m.group(0)); return f'@@CODE{len(codes)-1}@@'
text = re.sub(r'```.*?```', keep_code, text, flags=re.S)

maths = []
def keep(m, display):
    maths.append((m.group(1), display)); return f'@@MATH{len(maths)-1}@@'
text = re.sub(r'\$\$(.+?)\$\$', lambda m: keep(m, True), text, flags=re.S)
text = re.sub(r'(?<!\\)\$(.+?)(?<!\\)\$', lambda m: keep(m, False), text)
for i, c in enumerate(codes):
    text = text.replace(f'@@CODE{i}@@', c)

body = markdown.markdown(text, extensions=['tables', 'fenced_code'])
def restore(m):
    tex, disp = maths[int(m.group(1))]
    tex = html.escape(tex, quote=False)
    return f'<div class="eq">\\[{tex}\\]</div>' if disp else f'\\({tex}\\)'
body = re.sub(r'<p>@@MATH(\d+)@@</p>', restore, body)
body = re.sub(r'@@MATH(\d+)@@', restore, body)
assert '@@' not in body

page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>HiMCM 2026 A 数学模型讲解</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@600;700&family=JetBrains+Mono&display=swap">
<style>
@page {{ size: A4; margin: 20mm 18mm 22mm 18mm; }}
:root {{ --ink:#1b2130; --muted:#5a6375; --line:#d6dbe4; --accent:#2c5aa8; --soft:#eef2f9; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: "Noto Sans SC","WenQuanYi Zen Hei",sans-serif; color:var(--ink); font-size:10.5pt; line-height:1.7; margin:0; }}
h1 {{ font-family:"Noto Serif SC","WenQuanYi Zen Hei",serif; font-size:24pt; color:var(--accent); margin:0 0 6mm; padding-bottom:3mm; border-bottom:2px solid var(--accent); }}
h2 {{ font-family:"Noto Serif SC","WenQuanYi Zen Hei",serif; font-size:16pt; color:var(--accent); margin:0 0 3mm; break-before: page; break-after: avoid; }}
h1 + h2 {{ break-before: auto; margin-top: 2mm; }}
h3 {{ font-size:12pt; margin:5mm 0 2mm; break-after: avoid; }}
p {{ margin:1.6mm 0; }}
p:has(> strong:first-child) {{ }}
ul, ol {{ margin:1.5mm 0; padding-left:6mm; }}
li {{ margin:0.6mm 0; }}
table {{ border-collapse:collapse; width:100%; margin:2.5mm 0; font-size:9.5pt; break-inside: avoid; font-variant-numeric: tabular-nums; }}
th, td {{ border:1px solid var(--line); padding:1.4mm 2.2mm; vertical-align:middle; }}
th {{ background:var(--soft); font-weight:500; }}
.eq {{ margin:2.5mm 0; padding:2mm 3mm; background:var(--soft); border-radius:2mm; overflow-x:auto; break-inside: avoid; }}
pre {{ background:#f5f6f8; border:1px solid var(--line); border-radius:2mm; padding:3mm; font-size:9pt; break-inside: avoid; white-space:pre-wrap; }}
code {{ font-family:"JetBrains Mono",monospace; font-size:0.92em; }}
hr {{ display:none; }}
mjx-container[display="true"] {{ margin:0 !important; }}
</style>
<script>
window.MathJax = {{ tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] }}, svg: {{ fontCache:'global' }},
  startup: {{ pageReady: () => MathJax.startup.defaultPageReady().then(() => {{ document.body.dataset.mathDone = '1'; }}) }} }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script>
</head><body>{body}</body></html>'''
open(out_html, 'w', encoding='utf-8').write(page)
print('maths', len(maths))
