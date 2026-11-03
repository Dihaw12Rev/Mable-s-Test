// Picks the deal's primary company (falls back to the first associated company).
const res = arr(input.assoc);
const primary = res.find(r => (r.associationTypes || []).some(t => clean(t.label).toLowerCase() === "primary"));
const pick = primary || res[0];
return { companyId: pick ? clean(pick.toObjectId) : null, count: pick ? 1 : 0 };
