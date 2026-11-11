const { chromium } = require('playwright');
(async () => {
  const [src, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('console error:', m.text()); });
  await page.goto('file://' + src, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.body.dataset.mathDone === '1', null, { timeout: 120000 });
  await page.evaluate(() => document.fonts.ready);
  const errs = await page.evaluate(() => document.querySelectorAll('mjx-merror, [data-mjx-error]').length);
  console.log('mathjax errors:', errs);
  await page.pdf({
    path: out, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;font-size:8px;color:#888;text-align:center;font-family:sans-serif;">HiMCM 2026 A 数学模型讲解 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  });
  await browser.close();
})();
