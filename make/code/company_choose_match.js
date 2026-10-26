// Chooses ONE company from the search results.
//   1. Domain match. If several companies share the domain (e.g. facilities of one health
//      system), the one whose name also matches wins; otherwise the oldest record.
//   2. Otherwise an exact name match (ignoring case, punctuation and Inc/LLC/PC-style suffixes).
// Optional: details (the other portal's company fields). When given, fillBody holds only the
// fields that are BLANK on the matched company, so existing data is never overwritten.
const SUFFIXES = new Set(["inc", "incorporated", "llc", "pllc", "llp", "lp", "pc", "pa", "corp", "corporation",
    "co", "company", "ltd", "limited", "the"]);
const normName = v => clean(v).toLowerCase().replace(/\./g, "").replace(/&/g, " and ").replace(/[^a-z0-9 ]+/g, " ")
    .split(/\s+/).filter(w => w && !SUFFIXES.has(w)).join(" ");
const results = arr(input.search).slice().sort((a, b) => Number(a.id) - Number(b.id));
const domain = normDomain(input.domain);
const name = normName(input.name);
const nameOf = r => normName((r.properties || {}).name);

let match = null, matchedBy = "none", sharedDomain = 0;
if (domain) {
    const byDomain = results.filter(r => {
        const pr = r.properties || {};
        return normDomain(pr.domain) === domain || normDomain(pr.website) === domain;
    });
    sharedDomain = byDomain.length;
    if (byDomain.length === 1) { match = byDomain[0]; matchedBy = "domain"; }
    else if (byDomain.length > 1) {
        match = (name && byDomain.find(r => nameOf(r) === name)) || null;
        matchedBy = match ? "domain+name" : "domain (shared, oldest)";
        if (!match) match = byDomain[0];
    }
}
if (!match && name) {
    match = results.find(r => nameOf(r) === name) || null;
    if (match) matchedBy = "name";
}

const fill = {};
const details = input.details && typeof input.details === "object" ? input.details : {};
if (match) {
    const ours = match.properties || {};
    for (const k of ["domain", "address", "city", "state", "zip", "country"]) {
        if (clean(details[k]) && !clean(ours[k])) fill[k] = clean(details[k]);
    }
}
return {
    matchId: match ? clean(match.id) : null,
    matchedBy,
    sharedDomain,
    fillBody: JSON.stringify({ properties: fill }),
    fillCount: Object.keys(fill).length
};
