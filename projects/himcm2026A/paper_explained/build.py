"""Build the Chinese explained edition: python build.py [source.md output.pdf]  (needs: pip install markdown; Node.js + Playwright Chromium; internet for fonts/MathJax).
Source: paper_explained.md in this folder (a standalone copy of the paper with Chinese notes). The submission paper in ../paper is not touched."""
import html, re, subprocess, sys
from pathlib import Path
import markdown

HERE = Path(__file__).resolve().parent
LABEL = "HiMCM 2026 A · 中文讲解版（学习用，不提交）"
SRC, OUT = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("paper_explained.md", "HiMCM2026A_paper_explained_zh.pdf")
text = (HERE / SRC).read_text(encoding="utf-8")
text = re.sub(r"<div class=\"((?:summary-page|toc-page|toc|small|news|news-cols|refs|ai-report|news-box|news-two|zh|kp|cover-zh|chgeq)(?: [a-z-]+)*)\">", r'<div class="\1" markdown="1">', text)
maths = []
def keep(m, disp):
    maths.append((m.group(1), disp)); return f"@@MATH{len(maths) - 1}@@"
text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m, True), text, flags=re.S)
text = re.sub(r"\$(?=\d)", "&#36;", text)          # currency, not math
text = re.sub(r"(?<![\\$])\$(?!\s)(.+?)(?<!\s)\$", lambda m: keep(m, False), text)
body = markdown.markdown(text, extensions=["tables", "md_in_html", "sane_lists"])
def restore(m):
    tex, disp = maths[int(m.group(1))]
    tex = html.escape(tex, quote=False)
    return f'<div class="eq">\\[{tex}\\]</div>' if disp else f"\\({tex}\\)"
body = re.sub(r"<p>@@MATH(\d+)@@</p>", restore, body)
body = re.sub(r"@@MATH(\d+)@@", restore, body)
assert "@@" not in body
css = (HERE / "style.css").read_text(encoding="utf-8")
page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>HiMCM 2026 A 中文讲解版</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@400;600;700&family=Noto+Sans+SC:wght@400;700&family=Noto+Serif+SC:wght@400;700&display=swap">
<style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}},
startup:{{pageReady:()=>MathJax.startup.defaultPageReady().then(()=>{{document.body.dataset.mathDone='1';}})}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script></head><body>{body}</body></html>"""
(HERE / (Path(SRC).stem + ".html")).write_text(page, encoding="utf-8")
subprocess.run(["node", str(HERE / "render.js"), str(HERE / (Path(SRC).stem + ".html")), str(HERE / OUT), LABEL], check=True)
