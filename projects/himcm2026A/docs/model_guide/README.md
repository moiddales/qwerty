# 模型讲解（方法说明）

`HiMCM2026A_模型讲解.pdf` 用三城构造例子讲解方案中每个模型怎么算（底线约束、分段线性价值、稳健偏好线性规划、指数价值函数、SMAA、最小最大后悔、ELECTRE III、CES、Choquet、网络可达性、Poisson–Gamma、熵权法/CRITIC），数学只用 A-level P1/P3/S1。例子数字是构造的；真实 25 城结果见 [MODEL_RESULTS.md](../../MODEL_RESULTS.md)。

重新生成 PDF：

```bash
pip install markdown
python build.py guide.md guide.html
NODE_PATH=$(npm root -g) node render.js "$PWD/guide.html" "$PWD/HiMCM2026A_模型讲解.pdf"
```

render.js 需要 Node.js 与 Playwright（Chromium）；页面公式由 MathJax 3.2.2（jsdelivr）渲染，需要联网。
