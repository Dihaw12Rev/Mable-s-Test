// Render an HTML file to a Letter PDF with a page-numbered footer.
// Run after the matching build_*.py:
//   node render_pdf.js                                   (the Customer Onboarding SOP)
//   node render_pdf.js <in.html> <out.pdf> "<footer label>"
const path = require('path');
const { chromium } = require('playwright');

const [input = 'sop.html', output = 'RevGravy_Customer_Onboarding_SOP.pdf', label = 'RevGravy · Customer Onboarding SOP · v1.0'] = process.argv.slice(2);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(__dirname, input), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const footer = `<div style="width:100%;font-family:Inter,sans-serif;font-size:7pt;color:#5b6876;padding:0 0.7in;display:flex;justify-content:space-between">
    <span>${label}</span>
    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;
  await page.pdf({
    path: path.join(__dirname, output),
    format: 'Letter',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: footer,
  });
  await browser.close();
  console.log(`Saved ${output}`);
})();
