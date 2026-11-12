const { chromium } = require('playwright');
(async () => {
  const [src, out, team] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + src, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.body.dataset.mathDone === '1', null, { timeout: 120000 });
  await page.evaluate(() => document.fonts.ready);
  const errs = await page.evaluate(() => document.querySelectorAll('mjx-merror, [data-mjx-error]').length);
  if (errs) throw new Error('MathJax errors: ' + errs);
  await page.pdf({
    path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true,
    headerTemplate: `<div style="width:100%;font-size:7.5px;color:#666;font-family:Inter,sans-serif;padding:0 0.75in;display:flex;justify-content:space-between;"><span>Team # ${team}</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`,
    footerTemplate: '<div></div>',
  });
  await browser.close();
})();
