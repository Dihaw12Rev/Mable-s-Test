// Builds a company search for the OTHER portal: exact domain match OR exact name match.
// Input: company (GET company response body).
const p = (input.company && input.company.properties) || {};
const domain = normDomain(p.domain) || normDomain(p.website);
const name = clean(p.name);
const filterGroups = [];
if (domain) filterGroups.push({ filters: [{ propertyName: "domain", operator: "EQ", value: domain }] });
if (name) filterGroups.push({ filters: [{ propertyName: "name", operator: "EQ", value: name }] });
return {
    body: JSON.stringify({ filterGroups, properties: ["name", "domain", "website"], limit: 50 }),
    hasCriteria: filterGroups.length > 0,
    domain: domain || null,
    domainUrl: domain ? "https://" + domain : null,
    name: name || null,
    address: clean(p.address) || null,
    city: clean(p.city) || null,
    state: clean(p.state) || null,
    zip: clean(p.zip) || null,
    country: clean(p.country) || null,
    createBody: JSON.stringify({ properties: Object.fromEntries(Object.entries({ name, domain }).filter(([, v]) => v)) })
};
