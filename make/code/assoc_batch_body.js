// Builds a v4 default batch-association body from a list of records (e.g. upsert results)
// to one target record.
const ids = [...new Set(arr(input.records).map(r => clean(r.id)).filter(Boolean))];
return { body: JSON.stringify({ inputs: ids.map(id => ({ from: { id }, to: { id: clean(input.toId) } })) }), count: ids.length };
