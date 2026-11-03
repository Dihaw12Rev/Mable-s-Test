// Prepares a deal's existing notes to be copied to the other portal (backfill at deal
// creation). Skips notes that are themselves copies from the other portal.
// Inputs: notes (batch read body), owners (GET /crm/v3/owners body), label ("Nuance"/"MTMC"),
// skipPrefix (e.g. "[Note from MTMC Team"), fallbackRep (deal owner name).
const owners = {};
for (const o of arr(input.owners)) owners[clean(o.id)] = [clean(o.firstName), clean(o.lastName)].filter(Boolean).join(" ") || clean(o.email);
const label = clean(input.label);
const skipPrefix = clean(input.skipPrefix);
const fallbackRep = clean(input.fallbackRep);
const notes = [];
for (const n of arr(input.notes)) {
    const p = n.properties || {};
    if (!clean(p.hs_note_body)) continue;
    if (skipPrefix && stripHtml(p.hs_note_body).startsWith(skipPrefix)) continue;
    const rep = owners[clean(p.hubspot_owner_id)] || fallbackRep || "Unknown";
    notes.push({
        id: clean(n.id),
        body: `<p><strong>[Note from ${label} Team. Rep Name: ${escHtml(rep)}]</strong></p>${p.hs_note_body}`,
        timestamp: clean(p.hs_timestamp) || clean(p.hs_createdate) || new Date().toISOString(),
        modified: clean(p.hs_lastmodifieddate) || new Date().toISOString()
    });
}
notes.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
return { notes, count: notes.length };
