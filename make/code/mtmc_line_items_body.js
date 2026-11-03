// MTMC -> Nuance: builds the batch line-item body for the new MTMC Sync deal.
// Only line items supplied by Nuance (vendor) are copied, matching the line-item backfill.
// Set input.vendor to "" to copy every line item.
// Inputs: lineItems (batch read body), dealId, currency, vendor.
const vendor = clean(input.vendor).toLowerCase();
const deal = clean(input.dealId);
const curr = clean(input.currency) || "USD";
if (!deal) throw new Error("Missing dealId - cannot build line item associations.");
const toNumber = v => {
    if (v === null || v === undefined || v === "") return null;
    const n = parseFloat(String(v).replace(/[^0-9.\-]/g, ""));
    return isNaN(n) ? null : n;
};
const inputs = [];
let skippedOtherVendor = 0;
for (const item of arr(input.lineItems)) {
    const p = (item && item.properties) || {};
    const name = clean(p.name);
    if (!name) continue;
    const itemVendor = (clean(p.vendor__name) || clean(p.vendor_name)).toLowerCase();
    if (vendor && itemVendor !== vendor) { skippedOtherVendor++; continue; }
    const properties = { name, hs_line_item_currency_code: curr };
    const quantity = toNumber(p.quantity), price = toNumber(p.price);
    if (quantity !== null) properties.quantity = quantity;
    if (price !== null) properties.price = price;
    if (clean(p.hs_sku)) properties.hs_sku = clean(p.hs_sku);
    inputs.push({
        properties,
        associations: [{ to: { id: deal }, types: [{ associationCategory: "HUBSPOT_DEFINED", associationTypeId: 20 }] }]
    });
}
return { body: JSON.stringify({ inputs }), count: inputs.length, skippedOtherVendor };
