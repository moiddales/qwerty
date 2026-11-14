"""Build an English-only extract of the paper (no explanations) with the paper's own 12-pt style:
    python build_original.py member_B_original.md HiMCM2026A_member_B_original_en.pdf "label"
The extract is made from paper_explained.md by the ownership rules in make_guides.py; its text equals paper/paper.md."""
import html, re, subprocess, sys
from pathlib import Path
import markdown

HERE = Path(__file__).resolve().parent
src, out, label = sys.argv[1], sys.argv[2], sys.argv[3]
text = (HERE / src).read_text(encoding="utf-8")
text = re.sub(r"<div class=\"(summary-page|toc-page|toc|small|news|news-cols|refs|ai-report|news-box|news-two)\">", r'<div class="\1" markdown="1">', text)
maths = []
def keep(m, disp):
    maths.append((m.group(1), disp)); return f"@@MATH{len(maths) - 1}@@"
text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m, True), text, flags=re.S)
text = re.sub(r"\$(?=\d)", "&#36;", text)
text = re.sub(r"(?<![\\$])\$(?!\s)(.+?)(?<!\s)\$", lambda m: keep(m, False), text)
body = markdown.markdown(text, extensions=["tables", "md_in_html", "sane_lists"])
def restore(m):
    tex, disp = maths[int(m.group(1))]
    tex = html.escape(tex, quote=False)
    return f'<div class="eq">\\[{tex}\\]</div>' if disp else f"\\({tex}\\)"
body = re.sub(r"<p>@@MATH(\d+)@@</p>", restore, body)
body = re.sub(r"@@MATH(\d+)@@", restore, body)
assert "@@" not in body
css = (HERE.parent / "paper" / "style.css").read_text(encoding="utf-8") + """
.mb-title { font-family: Inter, sans-serif; font-size: 15pt; font-weight: 700; color: var(--accent); text-align: center; margin: 2pt 0 4pt; }
.omit { font-style: italic; color: #666; text-align: center; margin: 6pt 0; }"""
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(label)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Tinos:ital,wght@0,400;0,700;1,400&display=swap">
<style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}},
startup:{{pageReady:()=>MathJax.startup.defaultPageReady().then(()=>{{document.body.dataset.mathDone='1';}})}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script></head><body>{body}</body></html>"""
h = HERE / (Path(src).stem + ".html"); h.write_text(page, encoding="utf-8")
subprocess.run(["node", str(HERE / "render.js"), str(h), str(HERE / out), label], check=True)
