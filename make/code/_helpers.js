// --- shared helpers (prepended to every code module by build.py) ---
const arr = v => Array.isArray(v) ? v : (v && Array.isArray(v.results) ? v.results : []);
const clean = v => (v === null || v === undefined) ? "" : String(v).trim();
const normEmail = v => clean(v).toLowerCase();
function normDomain(v) {
    let s = clean(v).toLowerCase();
    if (!s) return "";
    s = s.replace(/^[a-z][a-z0-9+.-]*:\/\//, "").replace(/^www\./, "");
    return s.split(/[\/?#:\s]/)[0];
}
const stripHtml = h => clean(h).replace(/<[^>]*>/g, " ").replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/\s+/g, " ").trim();
const escHtml = s => clean(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
// --- end helpers ---
