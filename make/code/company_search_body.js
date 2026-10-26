// Builds a company search for the OTHER portal: exact domain match OR exact name match.
// Input: company (GET company response body).
const p = (input.company && input.company.properties) || {};
const domain = normDomain(p.domain) || normDomain(p.website);
const name = clean(p.name);
const filterGroups = [];
if (domain) filterGroups.push({ filters: [{ propertyName: "domain", operator: "EQ", value: domain }] });
if (name) filterGroups.push({ filters: [{ propertyName: "name", operator: "EQ", value: name }] });
// Details we can carry over: used to create a missing company, or to fill blanks on a match.
const details = Object.fromEntries(Object.entries({
    name, domain,
    address: clean(p.address), city: clean(p.city), state: clean(p.state), zip: clean(p.zip), country: clean(p.country)
}).filter(([, v]) => v));
return {
    body: JSON.stringify({
        filterGroups,
        properties: ["name", "domain", "website", "address", "city", "state", "zip", "country"],
        limit: 50
    }),
    hasCriteria: filterGroups.length > 0,
    domain: domain || null,
    domainUrl: domain ? "https://" + domain : null,
    name: name || null,
    address: details.address || null,
    city: details.city || null,
    state: details.state || null,
    zip: details.zip || null,
    country: details.country || null,
    details,
    createBody: JSON.stringify({ properties: details })
};
