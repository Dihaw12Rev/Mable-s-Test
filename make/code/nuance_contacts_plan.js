// Nuance -> MTMC: decides which contacts to create at MTMC (with the deal association
// included) and which existing MTMC contacts to associate. Existing MTMC contacts are
// never modified (per the guide).
const dealId = clean(input.dealId);
const existingByEmail = {};
for (const r of arr(input.existing)) {
    const em = normEmail((r.properties || {}).email);
    if (em) existingByEmail[em] = clean(r.id);
}
const toCreate = [], toAssociate = new Set(), seen = new Set();
for (const c of arr(input.contacts)) {
    const p = c.properties || {};
    const email = normEmail(p.email);
    if (email && existingByEmail[email]) { toAssociate.add(existingByEmail[email]); continue; }
    if (email) { if (seen.has(email)) continue; seen.add(email); }
    const properties = {};
    if (email) properties.email = email;
    for (const k of ["firstname", "lastname", "phone", "mobilephone", "jobtitle"]) if (clean(p[k])) properties[k] = clean(p[k]);
    if (!Object.keys(properties).length) continue;
    toCreate.push({
        properties,
        associations: [{ to: { id: dealId }, types: [{ associationCategory: "HUBSPOT_DEFINED", associationTypeId: 4 }] }]
    });
}
const assocInputs = [...toAssociate].map(id => ({ from: { id }, to: { id: dealId } }));
return {
    createBody: JSON.stringify({ inputs: toCreate }),
    createCount: toCreate.length,
    associateBody: JSON.stringify({ inputs: assocInputs }),
    associateCount: assocInputs.length
};
