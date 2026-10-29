// Copies a deal's associations to another deal in the same portal (e.g. the MTMC Sync copy gets
// the same contacts and companies as the original Cryodose deal). Only the "Primary" label is
// carried over. Builds a v4 batch-create body (deal -> X).
// Inputs: assoc (v4 association response of the source deal), dealId (target deal),
// typeId (unlabeled deal -> X type, e.g. 3 contacts / 341 companies),
// primaryTypeId (optional, e.g. 5 for the deal -> company primary label).
const dealId = clean(input.dealId);
if (!dealId) throw new Error("Missing dealId - cannot copy associations.");
const typeId = Number(input.typeId);
const primaryTypeId = Number(clean(input.primaryTypeId)) || null;
const seen = new Set(), inputs = [];
for (const r of arr(input.assoc)) {
    const id = clean(r && typeof r === "object" ? (r.toObjectId || r.id) : r);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    const types = [{ associationCategory: "HUBSPOT_DEFINED", associationTypeId: typeId }];
    const primary = ((r && r.associationTypes) || []).some(t => clean(t.label).toLowerCase() === "primary");
    if (primary && primaryTypeId) types.push({ associationCategory: "HUBSPOT_DEFINED", associationTypeId: primaryTypeId });
    inputs.push({ from: { id: dealId }, to: { id }, types });
}
return { body: JSON.stringify({ inputs }), count: inputs.length };
