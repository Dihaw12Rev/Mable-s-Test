// MTMC -> Nuance: builds a batch upsert by email (new contacts are created).
// Append-only by default (agreed with Nuance): an existing contact only gets the fields that
// are blank on our side; nothing we already have is overwritten. Needs our current values
// in input.existing. Set fillBlanksOnly=false to let MTMC values overwrite instead.
const fillBlanksOnly = !(input.fillBlanksOnly === false || clean(input.fillBlanksOnly) === "false");
const ours = {};
for (const r of arr(input.existing)) {
    const em = normEmail((r.properties || {}).email);
    if (em) ours[em] = r.properties || {};
}
const inputs = [], seen = new Set();
let skippedNoEmail = 0;
const unchanged = [];
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
    // Existing contact with nothing new to add: skip it (it is still linked to the deal below).
    if (ours[email] && Object.keys(properties).length === 1) { unchanged.push(email); continue; }
    inputs.push({ idProperty: "email", id: email, properties });
}
// IDs of existing contacts that needed no update, so they can still be linked to the deal.
const unchangedIds = arr(input.existing)
    .filter(r => unchanged.includes(normEmail((r.properties || {}).email)))
    .map(r => ({ id: clean(r.id) }));
return {
    body: JSON.stringify({ inputs }),
    count: inputs.length,
    unchangedIds,
    unchangedCount: unchangedIds.length,
    skippedNoEmail
};
