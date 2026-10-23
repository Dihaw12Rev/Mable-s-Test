// MTMC -> Nuance: builds a batch upsert by email. Only non-empty MTMC values are sent,
// so a blank field at MTMC never wipes our data. Set fillBlanksOnly=true (input) to
// skip fields we already have (needs the existing Nuance values in input.existing).
const fillBlanksOnly = input.fillBlanksOnly === true || clean(input.fillBlanksOnly) === "true";
const ours = {};
for (const r of arr(input.existing)) {
    const em = normEmail((r.properties || {}).email);
    if (em) ours[em] = r.properties || {};
}
const inputs = [], seen = new Set();
let skippedNoEmail = 0;
for (const c of arr(input.contacts)) {
    const p = c.properties || {};
    const email = normEmail(p.email);
    if (!email) { skippedNoEmail++; continue; }
    if (seen.has(email)) continue;
    seen.add(email);
    const properties = { email };
    for (const k of ["firstname", "lastname", "phone", "jobtitle"]) {
        if (!clean(p[k])) continue;
        if (fillBlanksOnly && ours[email] && clean(ours[email][k])) continue;
        properties[k] = clean(p[k]);
    }
    inputs.push({ idProperty: "email", id: email, properties });
}
return {
    body: JSON.stringify({ inputs }),
    count: inputs.length,
    skippedNoEmail
};
