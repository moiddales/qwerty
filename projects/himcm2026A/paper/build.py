"""Build the paper PDF: python build.py  (needs: pip install markdown; Node.js + Playwright Chromium; internet for fonts/MathJax)."""
import html, re, subprocess, sys
from pathlib import Path
import markdown

HERE = Path(__file__).resolve().parent
TEAM = sys.argv[1] if len(sys.argv) > 1 else "TEAM_NUMBER"
text = (HERE / "paper.md").read_text(encoding="utf-8") + "\n\n" + (HERE / "ai_report.md").read_text(encoding="utf-8")
text = text.replace("TEAM_NUMBER", TEAM)
text = re.sub(r"<div class=\"(summary-page|toc-page|toc|small|news|news-cols|refs|ai-report|news-box|news-two)\">", r'<div class="\1" markdown="1">', text)
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
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HiMCM 2026 Problem A</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@400;600;700&display=swap">
<style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}},
startup:{{pageReady:()=>MathJax.startup.defaultPageReady().then(()=>{{document.body.dataset.mathDone='1';}})}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script></head><body>{body}</body></html>"""
(HERE / "paper.html").write_text(page, encoding="utf-8")
subprocess.run(["node", str(HERE / "render.js"), str(HERE / "paper.html"), str(HERE / "HiMCM2026A_paper.pdf"), TEAM], check=True)
