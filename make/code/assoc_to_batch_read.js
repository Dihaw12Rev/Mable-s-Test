// Turns an association list into a batch-read body. Accepts a v4 association response
// ({results:[{toObjectId}]}), the native "List associations" output ([{id, type}]) or plain IDs.
// Inputs: assoc, properties (comma-separated).
const ids = [...new Set(arr(input.assoc).map(r => clean(r && typeof r === "object" ? (r.toObjectId || r.id) : r)).filter(Boolean))];
const properties = clean(input.properties).split(",").map(s => s.trim()).filter(Boolean);
return {
    body: JSON.stringify({ inputs: ids.map(id => ({ id })), properties }),
    count: ids.length
};
