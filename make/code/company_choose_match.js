// Chooses ONE company from the search results: domain match first, then exact name.
// Ties are broken by lowest record ID (oldest record) so the choice is stable.
const results = arr(input.search).slice().sort((a, b) => Number(a.id) - Number(b.id));
const domain = normDomain(input.domain);
const name = clean(input.name).toLowerCase();
let match = null, matchedBy = "none";
if (domain) {
    match = results.find(r => {
        const pr = r.properties || {};
        return normDomain(pr.domain) === domain || normDomain(pr.website) === domain;
    }) || null;
    if (match) matchedBy = "domain";
}
if (!match && name) {
    match = results.find(r => clean((r.properties || {}).name).toLowerCase() === name) || null;
    if (match) matchedBy = "name";
}
return { matchId: match ? clean(match.id) : null, matchedBy };
