// Notes sync: from the deals a note is attached to, picks the first one that is linked
// to the other portal. Inputs: deals (batch read body), linkProperty ("mtmc_deal_id" or
// "nuance_deal_id"), pipelines (optional comma-separated allow-list).
const allowed = clean(input.pipelines).split(",").map(s => s.trim()).filter(Boolean);
const deals = arr(input.deals).slice().sort((a, b) => Number(a.id) - Number(b.id));
const hit = deals.find(d => {
    const p = d.properties || {};
    if (!clean(p[clean(input.linkProperty)])) return false;
    return !allowed.length || allowed.includes(clean(p.pipeline));
});
const p = hit ? (hit.properties || {}) : {};
return {
    dealId: hit ? clean(hit.id) : null,
    linkedDealId: hit ? clean(p[clean(input.linkProperty)]) : null,
    dealOwnerId: clean(p.hubspot_owner_id) || null
};
