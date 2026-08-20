// Make Code module — matches MTMC line items to HOM products by SKU and
// builds the HubSpot (HOM) batch line-item body.
//
// A matched line item is created against the HOM product (hs_product_id), so
// it behaves like a line item picked from the HOM product library. An
// unmatched SKU falls back to a free-form line item — the deal total stays
// correct — and is reported back for follow-up.

// ---- Config ---------------------------------------------------------------
// "mtmc" carries the MTMC unit price across, keeping the HOM line items
// consistent with the deal amount copied from MTMC. "hom" prices the deal off
// the HOM catalog instead.
const PRICE_SOURCE = "mtmc";
// "hom" names the line item after the HOM product, so HOM's catalog naming
// wins. "mtmc" keeps the MTMC line item name.
const NAME_SOURCE = "hom";
// Create line items whose SKU has no HOM product as free-form line items.
const CREATE_UNMATCHED = true;
// ---------------------------------------------------------------------------

const items = Array.isArray(input.lineItems) ? input.lineItems : [];
const products = Array.isArray(input.homProducts) ? input.homProducts : [];
const deal = String(input.dealId || "").trim();
const curr = (input.currency || "USD").trim();

if (!deal) {
    throw new Error("Missing dealId — cannot build line item associations.");
}

function toNumber(val) {
    if (val === null || val === undefined || val === "") return null;
    const cleaned = String(val).replace(/[^0-9.\-]/g, "");
    const n = parseFloat(cleaned);
    return isNaN(n) ? null : n;
}

function normSku(val) {
    if (val === null || val === undefined) return "";
    return String(val).trim().toUpperCase();
}

// Index the HOM products by normalised SKU. First match wins; anything after
// that is a duplicate SKU in the HOM catalog and gets reported.
const bySku = {};
const duplicateSkus = [];

for (const product of products) {
    const props = (product && product.properties) ? product.properties : {};
    const key = normSku(props.hs_sku);
    if (!key) continue;

    if (bySku[key]) {
        duplicateSkus.push(props.hs_sku);
        continue;
    }

    bySku[key] = {
        id: String((product && product.id) || props.hs_object_id || "").trim(),
        name: props.name,
        price: props.price,
        description: props.description
    };
}

const inputs = [];
const unmatched = [];
let matchedCount = 0;

for (const item of items) {
    const props = (item && item.properties) ? item.properties : {};
    const mtmcName = (props.name ? String(props.name) : "").trim();
    const sku = props.hs_sku ? String(props.hs_sku).trim() : "";
    const match = bySku[normSku(sku)] || null;

    if (match) {
        matchedCount++;
    } else {
        unmatched.push({
            sku: sku,
            name: mtmcName,
            mtmcLineItemId: (item && item.id) ? String(item.id) : ""
        });
        if (!CREATE_UNMATCHED) continue;
    }

    const quantity = toNumber(props.quantity);
    const mtmcPrice = toNumber(props.price);
    const homPrice = match ? toNumber(match.price) : null;

    let price = mtmcPrice;
    if (match && PRICE_SOURCE === "hom" && homPrice !== null) price = homPrice;
    if (price === null && homPrice !== null) price = homPrice;

    let name = mtmcName;
    if (match && NAME_SOURCE === "hom" && match.name) name = String(match.name).trim();
    if (!name && match && match.name) name = String(match.name).trim();
    // HubSpot requires a name on every line item.
    if (!name) continue;

    const properties = {
        name: name,
        hs_line_item_currency_code: curr
    };
    if (quantity !== null) properties.quantity = quantity;
    if (price !== null) properties.price = price;
    if (sku) properties.hs_sku = sku;

    if (match && match.id) {
        // Links the line item to the HOM product record.
        properties.hs_product_id = match.id;
    } else if (props.description) {
        // Only carry the MTMC description when there is no HOM product to
        // inherit one from.
        properties.description = String(props.description);
    }

    inputs.push({
        properties: properties,
        associations: [
            {
                to: { id: deal },
                types: [
                    {
                        associationCategory: "HUBSPOT_DEFINED",
                        associationTypeId: 20
                    }
                ]
            }
        ]
    });
}

const body = { inputs: inputs };

const unmatchedSummary = unmatched
    .map(u => (u.sku || "(no SKU)") + " — " + (u.name || "(unnamed)"))
    .join("\n");

return {
    bodyString: JSON.stringify(body),
    count: inputs.length,
    matchedCount: matchedCount,
    unmatchedCount: unmatched.length,
    unmatched: unmatched,
    unmatchedSummary: unmatchedSummary,
    duplicateSkuCount: duplicateSkus.length
};
