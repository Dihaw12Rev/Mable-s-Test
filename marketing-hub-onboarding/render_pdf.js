// Render sop.html to RevGravy_Customer_Onboarding_SOP.pdf with page numbers.
// Run after build_sop_pdf.py:  node render_pdf.js
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(__dirname, 'sop.html'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const footer = `<div style="width:100%;font-family:Inter,sans-serif;font-size:7pt;color:#5b6876;padding:0 0.7in;display:flex;justify-content:space-between">
    <span>RevGravy · Customer Onboarding SOP · 2 November 2026</span>
    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;
  await page.pdf({
    path: path.join(__dirname, 'RevGravy_Customer_Onboarding_SOP.pdf'),
    format: 'Letter',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: footer,
  });
  await browser.close();
  console.log('Saved RevGravy_Customer_Onboarding_SOP.pdf');
})();
