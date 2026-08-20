// Make Code module — builds the HubSpot (HOM) product-search body.
// Collects the distinct SKUs on the MTMC line items so the next module can
// resolve them against the HOM product library in a single search call.

const items = Array.isArray(input.lineItems) ? input.lineItems : [];

// HubSpot search allows at most 100 values in an IN filter.
const MAX_VALUES = 100;

const seen = new Set();
const skus = [];
let blankSkuCount = 0;

for (const item of items) {
    const props = (item && item.properties) ? item.properties : {};
    const raw = props.hs_sku;
    const sku = (raw === null || raw === undefined) ? "" : String(raw).trim();

    if (!sku) {
        blankSkuCount++;
        continue;
    }

    const key = sku.toUpperCase();
    if (seen.has(key)) continue;
    seen.add(key);
    skus.push(sku);
}

const overflowCount = skus.length > MAX_VALUES ? skus.length - MAX_VALUES : 0;
const values = skus.slice(0, MAX_VALUES);

// Never send an empty IN list — HubSpot rejects it with a 400. The sentinel
// matches nothing, so a deal with no SKU-bearing line items still flows
// through instead of stopping the scenario here.
if (values.length === 0) values.push("__NO_SKU_MATCH__");

const body = {
    filterGroups: [
        {
            filters: [
                {
                    propertyName: "hs_sku",
                    operator: "IN",
                    values: values
                }
            ]
        }
    ],
    properties: ["hs_sku", "name", "price", "description", "hs_object_id"],
    limit: 100
};

return {
    searchBody: JSON.stringify(body),
    skuCount: skus.length,
    blankSkuCount: blankSkuCount,
    overflowCount: overflowCount
};
