// Builds a batch read BY EMAIL for the other portal from a list of contacts.
// Always sends at least one input so the call never fails on an empty list.
// Inputs: contacts (batch read body), properties (comma-separated, default "email").
const emails = [...new Set(arr(input.contacts).map(c => normEmail((c.properties || {}).email)).filter(Boolean))];
const properties = (clean(input.properties) || "email").split(",").map(s => s.trim()).filter(Boolean);
const inputs = (emails.length ? emails : ["no-contacts@sync.invalid"]).map(id => ({ id }));
return { body: JSON.stringify({ idProperty: "email", properties, inputs }), emailCount: emails.length };
