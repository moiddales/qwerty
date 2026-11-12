"""Build the marked study guides: the full guide (总版) and one guide per team member A–D.

    python make_guides.py            # writes guide_all.md, member_A.md … member_D.md and builds the PDFs

Body text and explanation boxes come from paper_explained.md (current). Each box is compared with the
original explained edition (git ed9e183, the 52-page version handed to the team); paper sentences are
compared with the paper text in that edition. Marks:
  - box badge 「本版新增」: box did not exist in the original edition;
  - box badge 「本版更新」: box existed but was changed; changed sentences are highlighted;
  - highlighted English sentences: paper text changed since the original edition.
B's front page is compared with the original member_B.md (git 56b0bf4) the same way.
"""
import difflib, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OLD_PE, OLD_B = "ed9e183", "56b0bf4"
REL = "projects/himcm2026A/paper_explained/"


def git_show(rev, name):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{REL}{name}"],
                          capture_output=True, text=True, check=True).stdout


# ---------------------------------------------------------------- parsing
def parse(text):
    """Items: ('box', cls, lines) for zh/kp boxes, ('line', None, [line]) otherwise."""
    lines = text.split("\n")
    items, i = [], 0
    while i < len(lines):
        m = re.match(r'<div class="(zh|kp)">', lines[i])
        if m:
            d, j = 0, i
            while True:
                d += lines[j].count("<div") - lines[j].count("</div>")
                if d == 0:
                    break
                j += 1
            items.append(["box", m.group(1), lines[i:j + 1]])
            i = j + 1
        else:
            items.append(["line", None, [lines[i]]])
            i += 1
    return items


PROT = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$|\*\*.+?\*\*|`[^`]+`|<[^>]+>|\[[^\]]*\]\([^)]*\)")


def sentences(s):
    """Split inline markdown into sentences without cutting math, bold, code, tags or links."""
    prot = [(m.start(), m.end()) for m in PROT.finditer(s)]
    inside = lambda k: any(a <= k < b for a, b in prot)
    cuts, k = [], 0
    while k < len(s):
        c = s[k]
        if not inside(k):
            if c in "。！？；":
                cuts.append(k + 1)
            elif c in ".?!" and k + 2 < len(s) and s[k + 1] == " " and (s[k + 2].isupper() or s[k + 2] in "($*"):
                cuts.append(k + 1)
        k += 1
    out, a = [], 0
    for c in cuts + [len(s)]:
        if s[a:c].strip():
            out.append(s[a:c])
        a = c
    return out


norm = lambda s: re.sub(r"\s+", "", s)


def split_cells(row):
    parts, cur, inmath = [], "", False
    for ch in row:
        if ch == "$":
            inmath = not inmath
        if ch == "|" and not inmath:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def units(lines):
    """Set of normalized sentences/cells of a block of markdown lines (for comparison)."""
    out = set()
    for l in lines:
        st = l.strip()
        if st.startswith("|"):
            out.update(norm(c) for c in split_cells(st) if c.strip())
        else:
            body = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", l)
            out.update(norm(s) for s in sentences(body))
    return out


def wrap(s):
    lead = len(s) - len(s.lstrip()); trail = len(s) - len(s.rstrip())
    core = s.strip()
    return s[:lead] + f'<span class="chg">{core}</span>' + (s[len(s) - trail:] if trail else "")


def mark_line(l, old):
    """Highlight the parts of one markdown line that are not in the old unit set."""
    st = l.strip()
    if st.startswith("$$") and st.endswith("$$") and len(st) > 4:
        return (l, False) if norm(st) in old else (f'<div class="chgeq">\n\n{st}\n\n</div>', True)
    if not st or st.startswith(("<", "#", "$$", "!", "\\")) or set(st) <= set("|-: "):
        return l, False
    if st.startswith("|"):
        cells = split_cells(l)
        changed = False
        for k in range(1, len(cells) - 1):
            c = cells[k]
            if c.strip() and norm(c) not in old:
                cells[k] = wrap(c); changed = True
        return "|".join(cells), changed
    m = re.match(r"^(\s*(?:[-*]|\d+\.)\s+)?(.*)$", l)
    pre, body = m.group(1) or "", m.group(2)
    if norm(body) in old:
        return l, False
    segs, changed = [], False
    for s in sentences(body):
        if norm(s) in old:
            segs.append(s)
        else:
            segs.append(wrap(s)); changed = True
    return pre + "".join(segs), changed


def mark_block(lines, old):
    out, n, inmath = [], 0, False
    for l in lines:
        if l.strip() == "$$":
            inmath = not inmath; out.append(l); continue
        if inmath:
            out.append(l); continue
        nl, ch = mark_line(l, old)
        out.append(nl); n += ch
    return out, n


def badge(lines, kind):
    tag = {"upd": '<span class="badge upd">本版更新</span>', "new": '<span class="badge new">本版新增</span>'}[kind]
    cls = re.match(r'<div class="(zh|kp)">', lines[0]).group(1)
    lines = [f'<div class="{cls} {kind}">'] + lines[1:]
    for k in range(1, len(lines)):
        if lines[k].strip():
            if lines[k].lstrip().startswith("**"):
                lines[k] = tag + " " + lines[k]
            else:
                lines[k:k] = [tag, ""]
            break
    return lines


def box_text(lines):
    return "\n".join(lines[1:-1]).strip()


# ---------------------------------------------------------------- marking the explained edition
cur_items = parse((HERE / "paper_explained.md").read_text(encoding="utf-8"))
old_items = parse(git_show(OLD_PE, "paper_explained.md"))
RAW = [L[0] for _, _, L in cur_items]          # unmarked first line of every item
old_boxes = [(cls, box_text(L)) for kind, cls, L in old_items if kind == "box"]
old_paper = units([L[0] for kind, _, L in old_items if kind == "line"])

stats = []          # (section, kind, title)
section = "封面"
for it in cur_items:
    kind, cls, L = it
    if kind == "line":
        h = re.match(r"^(#{1,2}) (.+)$", L[0]) or re.match(r'^<h1 class="refs-head">(.+)</h1>', L[0])
        if h:
            section = h.groups()[-1]
        for pat, name in ((r'<div class="summary-page">', "摘要页"), (r'<div class="news">', "12. 新闻稿"),
                          (r'<div class="ai-report">', "AI 使用报告")):
            if L[0].startswith(pat):
                section = name
        nl, ch = mark_line(L[0], old_paper) if not it[2][0].strip() == "$$" else (L[0], False)
        it[2] = [nl]
        continue
    text = box_text(L)
    same = [o for c, o in old_boxes if c == cls and o == text]
    first = text.split("\n")[0]
    for a, b in ((r"\Theta_S", "Θ_S"), (r"\Theta", "Θ"), (r"\theta^0", "θ⁰"), (r"\rho", "ρ"), (r"\tau", "τ"), ("\u3000", " ")):
        first = first.replace(a, b)
    title = "封面说明" if first.startswith("<div") else re.sub(r"[*$\\]", "", first)[:34]
    if same:
        continue
    best, ratio = None, 0.0
    for c, o in old_boxes:
        if c != cls:
            continue
        sm = difflib.SequenceMatcher(None, o, text, autojunk=False)
        if sm.real_quick_ratio() > ratio and sm.quick_ratio() > ratio:
            r = sm.ratio()
            if r > ratio:
                best, ratio = o, r
    if ratio < 0.4:
        it[2] = badge(L, "new"); stats.append((section, "新增", title))
    else:
        body, n = mark_block(L[1:-1], units(best.split("\n")))
        it[2] = badge([L[0]] + body + [L[-1]], "upd"); stats.append((section, "更新", title))

# display-math blocks in the paper text: no sentence marks inside; a formula that is new gets a marked frame
def formulas(items):
    out, k = [], 0
    while k < len(items):
        if items[k][0] == "line" and items[k][2][0].strip() == "$$":
            j = k + 1
            while not (items[j][0] == "line" and items[j][2][0].strip() == "$$"):
                j += 1
            out.append((k, j)); k = j + 1
        else:
            k += 1
    return out


old_forms = {norm("".join(L[0] for _, _, L in old_items[a + 1:b])) for a, b in formulas(old_items)}
for a, b in formulas(cur_items):
    for t in range(a + 1, b):
        cur_items[t][2] = [RAW[t]]
    if norm("".join(RAW[a + 1:b])) not in old_forms:
        cur_items[a][2] = ['<div class="chgeq">', "", "$$"]
        cur_items[b][2] = ["$$", "", "</div>"]


# ---------------------------------------------------------------- ownership
RULES = [  # (regex on the line, owner)
    (r'^<div class="summary-page">', "D"), (r'^<div class="toc-page">', "-"),
    (r"^# 1\. ", "B"), (r"^# 2\. ", "A"), (r"^# 3\. ", "B"), (r"^# 4\. ", "A"),
    (r"^# 5\. ", "P"), (r"^## 5\.1 ", "P"), (r"^## 5\.[23] ", "A"), (r"^## 5\.[45] ", "B"),
    (r"^## 5\.6 ", "C"), (r"^## 5\.7 ", "C"), (r"^\*\*ELECTRE III\*\* \[20\]", "D"), (r"^## 5\.8 ", "A"),
    (r"^# 6\. ", "H"), (r"^## 6\.[12] ", "A"), (r"^## 6\.[34] ", "B"), (r"^Table 1 gives the final ranking", "C"),
    (r"^\*\*Leave-one-statement-out", "B"), (r"^\*\*ELECTRE III\.\*\* With", "D"),
    (r"^# 7\. ", "D"), (r"^# 8\. ", "H"), (r"^## 8\.[12] ", "D"), (r"^## 8\.3 ", "C"), (r"^## 8\.4 ", "D"),
    (r"^## 8\.5 ", "B"), (r"^# 9\. ", "C"), (r"^# 1[01]\. ", "D"), (r'^<div class="news">', "C"),
    (r'^<h1 class="refs-head">', "A"), (r'^<div class="ai-report">', "D"),
]
owner, owners, sect, sects = "F", [], "", []
for (kind, cls, _), first in zip(cur_items, RAW):
    if kind == "line":
        L = [first]
        for pat, o in RULES:
            if re.match(pat, L[0]):
                owner = o
                break
        h = re.match(r"^#{1,2} (\d+(?:\.\d)?)", L[0])
        if h:
            sect = h.group(1)
    owners.append(owner); sects.append(sect)

# chapter headings ("H") are kept in a member's guide when the member owns something in that chapter
def owned(k, m):
    o = owners[k]
    if o == m or o == "P":
        return True
    if o == "H":
        for t in range(k + 1, len(cur_items)):
            if cur_items[t][0] == "line" and re.match(r"^# \d", RAW[t]):
                return False
            if owners[t] == m:
                return True
    return False


def first_words(t):
    if t.startswith("**Table 1."):
        return "表 1"
    t = t.replace("\\Theta", "Θ").replace("\\theta", "θ")
    t = re.sub(r"[*$\\]", "", t).strip().rstrip(".")
    b = re.match(r"^(.+?)\.\s", t)
    return f'"{b.group(1)}"' if b and len(b.group(1)) < 40 else '"' + " ".join(t.split()[:6]) + '"'


NAMES = {"A": "组员 A", "B": "组员 B", "C": "组员 C", "D": "组员 D"}
SPLIT = ("5.7", "6.4")


def member_body(m):
    n = len(cur_items)
    owns_in = lambda sec: any(owners[t] == m and sects[t] == sec for t in range(n))
    keep = [owned(k, m) or (cur_items[k][0] == "line" and RAW[k].startswith("## ") and sects[k] in SPLIT and owns_in(sects[k]))
            for k in range(n)]
    out, k = [], 0
    while k < n:
        if keep[k]:
            out += cur_items[k][2]; k += 1; continue
        j = k
        while j < n and not keep[j]:
            j += 1
        sec = sects[k]
        if sec in SPLIT and owns_in(sec):
            heads, who = [], []
            for t in range(k, j):
                if sects[t] != sec:
                    break
                if cur_items[t][0] == "line" and re.match(r"^(\*\*|[A-Z][a-z ])", RAW[t]):
                    heads.append(first_words(RAW[t]))
                if owners[t] in NAMES and NAMES[owners[t]] not in who:
                    who.append(NAMES[owners[t]])
            out += ["", '<div class="zh skip">', "", f"**（{sec} 节的{'、'.join(heads)}归{'、'.join(who)}，这里略去。）**", "", "</div>", ""]
        k = j
    return out


# ---------------------------------------------------------------- front pages
LEGEND = """**标记说明（对照 2026-11-12 发给全组的原讲解版，52 页）**

| 标记 | 含义 |
|---|---|
| <span class="badge upd">本版更新</span> | 原讲解版就有这个讲解框，本版按修改后的论文改过；框里<span class="chg">这样高亮的句子</span>是改写或新加的，其余句子与原讲解版一字不差 |
| <span class="badge new">本版新增</span> | 原讲解版没有这个讲解框，是本版为新增的论文内容写的 |
| 英文原文中<span class="chg">高亮的句子</span> | 论文原文本版改过的句子；新增或改过的整行公式用同样的底色框出 |
| 无标记 | 与原讲解版完全相同 |
"""

PARTS = {  # member -> [(label, start marker, description)] ; description from the team assignment
    "A": [("第 2 章 假设", "# 2. ", "六条假设各自的理由；假设 5（可以部分补偿）就是加权求和"),
          ("第 4 章 数据", "# 4. ", "长表如何汇总成 25×20 矩阵；人口加权平均；Chicago 犯罪改用警察局口径（960）；四种误差来源和 7 个零误差指标；缺失值的中位数填补和名次范围"),
          ("5.1 记号", "## 5.1 ", "每个符号的含义；点积 φᵀθ"),
          ("5.2 底线", "## 5.2 ", "三道底线和各自依据；交通死亡为什么不再是底线；为什么在加权前检查；通过 / 待定 / 不通过；20,000 次模拟"),
          ("5.3 分段线性价值", "## 5.3 ", "φ 的截断公式；“越小越好”自动处理；为什么没有单独的权重；固定参考点"),
          ("5.8 算例", "## 5.8 ", "手算先修课指标：0.0472 对 0.0393；七个领域合计 0.8205 对 0.8210"),
          ("6.1 参考成绩单、图 1", "## 6.1 ", "Denver 和 Seattle 只差 0.0005；只有数据误差时 Denver 52.5%、Seattle 47.5%；New York 第三"),
          ("6.2 底线结果", "## 6.2 ", "San Francisco 50.4% 不通过，收入过 80,616 美元即通过；三个待定城市；Bonferroni 下界"),
          ("第 13 章 参考文献", '<h1 class="refs-head">', "[1]–[17] 数据、[18]–[20] 方法、[21]–[25] 检验与方法、[26] NHTS")],
    "B": [("5.1 记号（先修，属于 A）", "## 5.1 ", "看懂 $x$、$\\phi$、$\\theta$、$\\Theta$、$U$ 这几个符号，后面全靠它们"),
          ("第 1 章 引言", "# 1. ", "题目要求、我们对\"最好\"的定义、\"不能依赖开车接送\"的含义、流程图"),
          ("第 3 章 指标", "# 3. ", "七个领域、二十个指标、四个节点、公交可达性编码、舍弃的指标、balance"),
          ("5.4 偏好集合", "## 5.4 ", "什么样的权重算\"合理\"：$\\Theta$、$\\theta^0$、$\\Theta_S$"),
          ("5.5 线性规划", "## 5.5 ", "怎么证明\"对所有合理权重都成立\""),
          ("6.3 宽集合下的结果", "## 6.3 ", "在 $\\Theta$ 下什么都定不下来"),
          ("6.4 的四段", "## 6.4 ", "加上 P1–P6 后：7 对确定、6 城不可能第一、$\\theta^0$ 在边界、为什么加 P6、逐条去掉陈述"),
          ("8.5 需要多少共识", "## 8.5 ", "分歧主要在领域内部")],
    "C": [("5.1 记号（先修，属于 A）", "## 5.1 ", "看懂 $x$、$\\phi$、$\\theta$、$\\Theta$、$U$ 这几个符号，后面全靠它们"),
          ("5.6 SMAA", "## 5.6 ", "(a)–(d) 四步；最终权重是三层份额的乘积；拒绝抽样与通过率；排名规则；第一名比例、平均名次、中心权重、置信因子的公式；标准误与三对并列"),
          ("5.7 前半段 极小化最大后悔", "## 5.7 ", "后悔的定义；两个 max 为什么能交换；三城市例子"),
          ("6.4 中的表 1 与解读", "Table 1 gives the final ranking", "表 1 每一列和 ‡ 并列标记；为什么是 Seattle；New York、Denver、Chicago 落后的原因"),
          ("8.3 敏感性分析、图 4", "## 8.3 ", "领域权重扫描；节点 ±10%；误差放大与误差同向；逐个去掉指标；其他数据选择；泊松–伽马；在 Θ_S 下重做的检验"),
          ("第 9 章 谁该选哪个城市、图 6、图 7", "# 9. ", "六类学生；收入与房租底线；城市内部：Seattle 仅 38.5%；对数坐标"),
          ("第 12 章 新闻稿", '<div class="news">', "新闻稿怎么用大白话讲底线和 SMAA；四舍五入后的数字对应论文哪个数")],
    "D": [("5.1 记号（先修，属于 A）", "## 5.1 ", "看懂 $x$、$\\phi$、$\\theta$、$\\Theta$、$U$ 这几个符号，后面全靠它们"),
          ("摘要页", '<div class="summary-page">', "定义、模型五步、结果、修订、可信度、提醒，各用一句话讲清"),
          ("5.7 后半段 ELECTRE III", "**ELECTRE III** [20]", "0–1 分数 g 和权重 W 的来历；和谐度、不和谐度、否决；可信度公式；区分阈值 0.30 − 0.15σ；提炼；核心；抽样版"),
          ("6.4 中的 ELECTRE 结果段", "**ELECTRE III.** With", "参考权重下核心是 Austin 和 Denver；400 组权重下 Seattle 88%、Austin 35%、Denver 13%"),
          ("第 7 章 两次修订、图 3", "# 7. ", "−99999 缺失编码与成人特许学校；控制变量比较；从服务量到可达性；τ = 0.887、0.967"),
          ("8.1 熵权法", "## 8.1 ", "删一城熵权法颠倒 106 对、我们 0 对；为什么熵权会把 New York 推成第一"),
          ("8.2 其他加总规则", "## 8.2 ", "各规则的公式；线性、指数、CES、Choquet、熵权 / CRITIC 各选出谁"),
          ("8.4 外部检验", "## 8.4 ", "六项外部结果和 ρ；霸凌那一项为什么不吻合"),
          ("第 10 章 优缺点", "# 10. ", "五条优点；六条缺点及各自的改进办法"),
          ("第 11 章 结论", "# 11. ", "五条结论对应题目哪项要求"),
          ("AI 使用报告", '<div class="ai-report">', "两个工具各做了什么；发现并改正的三个问题")],
}
TITLES = {"A": "测量与打分", "B": "偏好集合与线性规划", "C": "SMAA 与后悔值", "D": "不可补偿规则与对照方法"}
CARDS = {"A": "K1（向量与点积）、K2（集合记号）、K3（正态 90% 区间）、K4（截断与分段线性）、K8（蒙特卡洛）、K10（标准误）、K14（Bonferroni 下界）、K15（泊松分布与 √n）",
         "B": "K1（向量与点积）、K2（集合记号）、K5（凹性）、K6（线性规划）、K7（必然偏好、可能偏好、可能赢家）",
         "C": "K9（单纯形上的均匀抽样与拒绝抽样）、K11（SMAA 的输出）、K12（极小化最大后悔）、K20（泊松–伽马与收缩）；先修 K1、K2",
         "D": "K13（ELECTRE III）、K16（斯皮尔曼 ρ）、K17（肯德尔 τ）、K18（熵权法与 CRITIC）、K19（CES 与 Choquet）；先修 K1、K2"}
ORDER = {"A": "先读 5.1 记号和 K1、K2，再按第 2 章 → 第 4 章 → 5.2 → 5.3 → 5.8 → 6.1 → 6.2 → 第 13 章的顺序读。5.3 和 5.8 是重点，最好拿纸笔把 5.8 的先修课指标算一遍。",
         "C": "先读 5.1 记号和 K1、K2，再按 5.6 → 5.7 前半段 → 6.4 的表 1 → 8.3 → 第 9 章 → 第 12 章的顺序读。5.6 是重点，K9 和 K11 要和 5.6 的 (a)–(d) 四步对照着读。",
         "D": "先读 5.1 记号和 K1、K2，再按 5.7 后半段（K13）→ 6.4 的 ELECTRE 段 → 第 7 章 → 8.1 → 8.2 → 8.4 → 第 10、11 章 → 摘要页 → AI 使用报告的顺序读。摘要页放在最后读，因为它概括的是全文。"}
PREREQ = {"C": "后面的 SMAA 抽样、排名和后悔值全部用这些符号写成。",
          "D": "后面的 ELECTRE III 和各种加总规则全部用这些符号写成。"}


def find_line(marker):
    for k, (kind, _, L) in enumerate(cur_items):
        if kind == "line" and RAW[k].startswith(marker):
            return k
    raise KeyError(marker)


def front(m, pages):
    rows = "\n".join(f"| {lab} | {pages.get((m, lab), '')} | {desc} |" for lab, _, desc in PARTS[m])
    what = (f"**这份文档是什么。** 只收组员 {m} 负责的部分：英文原文照抄，每段后面接中文讲解（米黄色框），课程外的知识写成补充知识卡（绿色框）。"
            f"原文和讲解与全文讲解总版完全一致，这里只是把你的部分单独拿出来；表中页码指总版的页码。")
    head = [f'<div class="cover-zh">', "", f"**HiMCM 2026 A 论文 · 组员 {m} 专用讲解**", "", f"**{TITLES[m]}**", "", "</div>", "", what, "",
            LEGEND, "", "**你负责的内容**", "", "| 部分 | 总版页码 | 一句话说明 |", "|---|---|---|", rows, "",
            f"补充知识卡：{CARDS[m]}。", ""]
    if m == "B":
        src = (HERE / "member_B_front.md").read_text(encoding="utf-8")
        old_front = git_show(OLD_B, "member_B.md").split("## 5.1 Notation")[0]
        body, _ = mark_block(src.split("\n"), units(old_front.split("\n")))
        head += body
    else:
        head += [f"**建议学习顺序**：{ORDER[m]}", ""]
        if m != "A":
            head += ['<div class="zh">', "", f"**先修：5.1 记号（属于组员 A，你必须看懂）。** {PREREQ[m]}", "", "</div>", ""]
    return head


def all_front(pages):
    team = (HERE / "team_assignment.md").read_text(encoding="utf-8")
    overview = re.search(r"\| 组员 \| 主题.*?\n\n", team, re.S).group(0).strip()
    overview = re.sub(r"（姓名：　）", "", overview)
    n_upd = sum(1 for s in stats if s[1] == "更新"); n_new = sum(1 for s in stats if s[1] == "新增")
    n_box = sum(1 for kind, _, _ in cur_items if kind == "box")
    rows = "\n".join(f"| {sec} | {kind} | {title} |" for sec, kind, title in stats)
    return ['<div class="cover-zh">', "", "**HiMCM 2026 A 论文 · 中文讲解总版**", "", "**全文讲解 + 分工 + 本版改动标记**", "", "</div>", "",
            "**这份文档是什么。** 全文英文原文照抄，每段后面接中文讲解（米黄色框），课程外的知识写成补充知识卡（绿色框）。"
            "讲解来自 2026-11-12 发给全组的原讲解版；论文按审计修改后，只改动受影响的讲解框，并在下面标出。"
            "四人的专用讲解都是从这份总版里切出来的，内容一致。", "",
            LEGEND, "", "**分工总览**", "", overview, "",
            f"**本版改动的讲解框**：全文共 {n_box} 个讲解框和知识卡，其中 {n_upd} 个更新、{n_new} 个新增，其余与原讲解版相同。", "",
            '<div class="small">', "", "| 位置 | 改动 | 讲解框开头 |", "|---|---|---|", rows, "", "</div>", "",
            '<div class="pb"></div>', ""]


# ---------------------------------------------------------------- page numbers from the built full guide
def pdf_pages(pdf):
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return out.split("\f")


def locate(pages_txt, needle, start=0):
    key = norm(needle)[:28]
    for p in range(start, len(pages_txt)):
        if key in norm(pages_txt[p]):
            return p + 1
    return None


def marker_text(marker):
    k = find_line(marker)
    t = RAW[k]
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[#*]", "", t).strip()
    if marker.startswith("<div class=\"summary-page\">"):
        return "2026 HiMCM Summary Sheet"
    if marker.startswith("<div class=\"news\">"):
        return "Seattle Tops Our Ranking"
    if marker.startswith("<div class=\"ai-report\">"):
        return "Report on Use of AI Tools"
    return t[:40]


def compute_pages(pdf):
    txt = pdf_pages(pdf)
    summary = locate(txt, "2026 HiMCM Summary Sheet") - 1
    intro = locate(txt, "More than 15 million students attend", summary) - 1
    starts = {}
    for m, parts in PARTS.items():
        for lab, marker, _ in parts:
            starts[(m, lab)] = (find_line(marker), locate(txt, marker_text(marker), summary if "summary" in marker else intro))
    # end page: page before the next owned-by-someone-else start (approximate by next part start in document order)
    allstarts = sorted({v for v in starts.values()} | {(find_line('<div class="toc-page">'), locate(txt, "Contents", summary))})
    pages = {}
    for key, (k, p) in starts.items():
        nxt = [q for kk, q in allstarts if kk > k]
        end = nxt[0] if nxt else len(txt) - 1
        # section continues to the page where the next section starts (same page if it starts mid-page)
        pages[key] = f"{p}" if end <= p else f"{p}–{end}"
    return pages


# ---------------------------------------------------------------- write + build
CSS_EXTRA = """
/* ---- study-guide marks ---- */
.badge { display:inline-block; font-family:"Noto Sans SC",Inter,sans-serif; font-size:7.6pt; font-weight:700; color:#fff; border-radius:2pt; padding:0.5pt 4pt; margin-right:3pt; vertical-align:1pt; }
.badge.upd { background:#c2410c; } .badge.new { background:#9f1239; }
.zh.upd { border-left-color:#c2410c; } .kp.upd { border-left-color:#c2410c; }
.zh.new { border-left-color:#9f1239; background:#fbf1ee; } .kp.new { border-left-color:#9f1239; }
.zh.skip { background:#f4f4f2; border-left-color:#999; }
.chg { background:#ffe1cf; border-bottom:1px solid #e8590c; -webkit-box-decoration-break:clone; box-decoration-break:clone; }
.pb { break-after: page; }
.chgeq { background:#ffe1cf; border-left:3px solid #e8590c; padding:1pt 0; margin:4pt 0; }
"""


def build(md_name, pdf_name):
    subprocess.run([sys.executable, str(HERE / "build.py"), md_name, pdf_name], check=True, cwd=HERE)


def main():
    css = (HERE / "style.css").read_text(encoding="utf-8")
    if "study-guide marks" not in css:
        (HERE / "style.css").write_text(css.rstrip("\n") + "\n" + CSS_EXTRA, encoding="utf-8")
    body_all = [l for it in cur_items for l in it[2]]
    pages = {}
    for rnd in range(2):     # the front page lists page numbers, so build twice
        (HERE / "guide_all.md").write_text("\n".join(all_front(pages) + body_all), encoding="utf-8")
        build("guide_all.md", "HiMCM2026A_guide_all_zh.pdf")
        pages = compute_pages(HERE / "HiMCM2026A_guide_all_zh.pdf")
    for m in "ABCD":
        (HERE / f"member_{m}.md").write_text("\n".join(front(m, pages) + [""] + member_body(m)), encoding="utf-8")
        build(f"member_{m}.md", f"HiMCM2026A_member_{m}_zh.pdf")
    print("boxes changed:", len(stats), "updated", sum(s[1] == "更新" for s in stats), "new", sum(s[1] == "新增" for s in stats))


if __name__ == "__main__":
    main()
