// Chooses ONE company from the search results (rule agreed with Nuance):
//   1. Domain match. If several companies share the domain (e.g. facilities of one health
//      system), the one whose name also matches wins; otherwise the oldest record.
//   2. Otherwise an exact company name match (case-insensitive, extra spaces ignored).
//   3. No match: matchId is null and the caller creates a new company.
// A matched company is only linked; it is never edited.
const exactName = v => clean(v).toLowerCase().replace(/\s+/g, " ");
const results = arr(input.search).slice().sort((a, b) => Number(a.id) - Number(b.id));
const domain = normDomain(input.domain);
const name = exactName(input.name);
const nameOf = r => exactName((r.properties || {}).name);

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
return { matchId: match ? clean(match.id) : null, matchedBy, sharedDomain };
