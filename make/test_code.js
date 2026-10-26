// Unit tests for the Make Code modules: node make/test_code.js
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const dir = path.join(__dirname, "code");
const helpers = fs.readFileSync(path.join(dir, "_helpers.js"), "utf8");
const run = (file, input) => new Function("input", helpers + "\n" + fs.readFileSync(path.join(dir, file), "utf8"))(input);
let passed = 0;
const test = (name, fn) => { fn(); passed++; console.log("ok -", name); };

test("assoc_to_batch_read: v4 response, native list, empty", () => {
    let r = run("assoc_to_batch_read.js", { assoc: { results: [{ toObjectId: 11 }, { toObjectId: 11 }, { toObjectId: 12 }] }, properties: "email, firstname" });
    assert.deepStrictEqual(JSON.parse(r.body), { inputs: [{ id: "11" }, { id: "12" }], properties: ["email", "firstname"] });
    assert.strictEqual(r.count, 2);
    r = run("assoc_to_batch_read.js", { assoc: [{ id: "5", type: "note_to_deal" }, { id: "5", type: "x" }], properties: "a" });
    assert.strictEqual(r.count, 1);
    assert.strictEqual(run("assoc_to_batch_read.js", { assoc: undefined, properties: "a" }).count, 0);
});

test("pick_primary_company prefers Primary label", () => {
    const r = run("pick_primary_company.js", { assoc: { results: [
        { toObjectId: 1, associationTypes: [{ label: null }] },
        { toObjectId: 2, associationTypes: [{ label: "Primary" }] }] } });
    assert.strictEqual(r.companyId, "2");
    assert.strictEqual(run("pick_primary_company.js", { assoc: { results: [] } }).companyId, null);
});

test("company_search_body normalizes domain / website and handles blanks", () => {
    let r = run("company_search_body.js", { company: { properties: { name: " Westchester Foot Care ", domain: "", website: "https://www.WestchesterFoot.com/about" } } });
    assert.strictEqual(r.domain, "westchesterfoot.com");
    assert.strictEqual(r.domainUrl, "https://westchesterfoot.com");
    const b = JSON.parse(r.body);
    assert.strictEqual(b.filterGroups.length, 2);
    assert.strictEqual(b.filterGroups[0].filters[0].value, "westchesterfoot.com");
    assert.strictEqual(b.filterGroups[1].filters[0].value, "Westchester Foot Care");
    assert.deepStrictEqual(JSON.parse(r.createBody), { properties: { name: "Westchester Foot Care", domain: "westchesterfoot.com" } });
    r = run("company_search_body.js", { company: { properties: { name: "Acme", domain: "acme.com", city: "Rye", zip: "10580", state: "" } } });
    assert.deepStrictEqual(r.details, { name: "Acme", domain: "acme.com", city: "Rye", zip: "10580" });
    assert.deepStrictEqual(JSON.parse(r.createBody).properties, r.details);   // new company gets the full address
    r = run("company_search_body.js", { company: { properties: { name: "", domain: "" } } });
    assert.strictEqual(r.hasCriteria, false);   // blank company never matches a random record
});

test("company_choose_match: shared health-system domain prefers the name match", () => {
    const search = { results: [
        { id: "100", properties: { name: "NYU Langone Health", domain: "nyulangone.org" } },
        { id: "200", properties: { name: "NYU Langone Orthopedics, Inc.", domain: "nyulangone.org", city: "" } }] };
    let r = run("company_choose_match.js", { search, domain: "nyulangone.org", name: "NYU Langone Orthopedics" });
    assert.strictEqual(r.matchId, "200");
    assert.strictEqual(r.matchedBy, "domain+name");
    assert.strictEqual(r.sharedDomain, 2);
    r = run("company_choose_match.js", { search, domain: "nyulangone.org", name: "Some Other Clinic" });
    assert.deepStrictEqual([r.matchId, r.matchedBy], ["100", "domain (shared, oldest)"]);
});

test("company_choose_match: name step ignores punctuation and Inc/LLC/PC", () => {
    const search = { results: [{ id: "7", properties: { name: "Westchester Foot Care, P.C.", domain: "" } }] };
    const r = run("company_choose_match.js", { search, domain: "", name: "westchester foot care pc" });
    assert.deepStrictEqual([r.matchId, r.matchedBy], ["7", "name"]);
});

test("company_choose_match: only blank fields are filled on a matched company", () => {
    const search = { results: [{ id: "9", properties: { name: "Acme", domain: "acme.com", address: "1 Main St", city: "", zip: null } }] };
    const r = run("company_choose_match.js", { search, domain: "acme.com", name: "Acme",
        details: { name: "ACME Podiatry", domain: "acme.com", address: "99 Other Rd", city: "Rye", zip: "10580" } });
    assert.deepStrictEqual(JSON.parse(r.fillBody).properties, { city: "Rye", zip: "10580" });
    assert.strictEqual(r.fillCount, 2);
    assert.strictEqual(run("company_choose_match.js", { search, domain: "acme.com", name: "Acme" }).fillCount, 0);
});

test("company_choose_match: domain beats name, stable tie-break, no match", () => {
    const search = { results: [
        { id: "900", properties: { name: "Acme Clinic", domain: "other.com" } },
        { id: "500", properties: { name: "Acme Podiatry", domain: "acme.com" } },
        { id: "300", properties: { name: "Acme Podiatry LLC", website: "http://www.acme.com" } }] };
    const pick = r => [r.matchId, r.matchedBy];
    // Domain beats a name match on another domain; two records share acme.com, so the oldest wins.
    let r = run("company_choose_match.js", { search, domain: "acme.com", name: "Acme Clinic" });
    assert.deepStrictEqual(pick(r), ["300", "domain (shared, oldest)"]);
    // ...unless one of them also matches the name (suffix-insensitive).
    r = run("company_choose_match.js", { search, domain: "acme.com", name: "Acme Podiatry" });
    assert.deepStrictEqual(pick(r), ["300", "domain+name"]);
    r = run("company_choose_match.js", { search: { results: [search.results[1]] }, domain: "acme.com", name: "Whatever" });
    assert.deepStrictEqual(pick(r), ["500", "domain"]);
    r = run("company_choose_match.js", { search, domain: "nomatch.com", name: "acme clinic" });
    assert.deepStrictEqual(pick(r), ["900", "name"]);
    r = run("company_choose_match.js", { search: { results: [] }, domain: "x.com", name: "X" });
    assert.deepStrictEqual(pick(r), [null, "none"]);
});

test("contacts_read_by_email_body never sends an empty list", () => {
    let r = run("contacts_read_by_email_body.js", { contacts: { results: [] } });
    assert.strictEqual(r.emailCount, 0);
    assert.strictEqual(JSON.parse(r.body).inputs.length, 1);
    r = run("contacts_read_by_email_body.js", { contacts: { results: [{ properties: { email: "A@B.com " } }, { properties: { email: "a@b.com" } }] }, properties: "email,phone" });
    assert.deepStrictEqual(JSON.parse(r.body), { idProperty: "email", properties: ["email", "phone"], inputs: [{ id: "a@b.com" }] });
});

test("nuance_contacts_plan: existing linked untouched, new created with deal association", () => {
    const r = run("nuance_contacts_plan.js", {
        dealId: 777,
        contacts: { results: [
            { id: "1", properties: { email: "Old@x.com", firstname: "Ann" } },
            { id: "2", properties: { email: "new@x.com", firstname: "Bo", lastname: "Li", phone: "555", jobtitle: "DPM" } },
            { id: "3", properties: { email: "", firstname: "NoEmail" } }] },
        existing: { results: [{ id: "4001", properties: { email: "old@x.com" } }], errors: [{ status: "error" }] }
    });
    assert.strictEqual(r.associateCount, 1);
    assert.deepStrictEqual(JSON.parse(r.associateBody).inputs, [{ from: { id: "4001" }, to: { id: "777" } }]);
    const created = JSON.parse(r.createBody).inputs;
    assert.strictEqual(r.createCount, 2);
    assert.deepStrictEqual(created[0].properties, { email: "new@x.com", firstname: "Bo", lastname: "Li", phone: "555", jobtitle: "DPM" });
    assert.strictEqual(created[0].associations[0].types[0].associationTypeId, 4);
});

test("mtmc_contacts_upsert_body: skips no-email, never sends blanks, fill-blanks mode", () => {
    const contacts = { results: [
        { properties: { email: "A@x.com", firstname: "Ann", lastname: "", phone: "999" } },
        { properties: { email: "", firstname: "Ghost" } }] };
    let r = run("mtmc_contacts_upsert_body.js", { contacts, existing: { results: [] } });
    assert.strictEqual(r.count, 1);
    assert.strictEqual(r.skippedNoEmail, 1);
    assert.deepStrictEqual(JSON.parse(r.body).inputs[0], { idProperty: "email", id: "a@x.com", properties: { email: "a@x.com", firstname: "Ann", phone: "999" } });
    // Default is append-only: our first name stays, the blank phone is filled.
    r = run("mtmc_contacts_upsert_body.js", { contacts, existing: { results: [{ id: "55", properties: { email: "a@x.com", firstname: "Annie", phone: "" } }] } });
    assert.deepStrictEqual(JSON.parse(r.body).inputs[0].properties, { email: "a@x.com", phone: "999" });
    // Overwrite mode still available when explicitly asked for.
    r = run("mtmc_contacts_upsert_body.js", { contacts, existing: { results: [{ id: "55", properties: { email: "a@x.com", firstname: "Annie" } }] }, fillBlanksOnly: "false" });
    assert.strictEqual(JSON.parse(r.body).inputs[0].properties.firstname, "Ann");
});

test("mtmc_contacts_upsert_body: complete existing contacts are not updated but still linked", () => {
    const r = run("mtmc_contacts_upsert_body.js", {
        contacts: { results: [{ properties: { email: "full@x.com", firstname: "MTMC Name", phone: "111" } }] },
        existing: { results: [{ id: "77", properties: { email: "full@x.com", firstname: "Ours", phone: "222" } }] },
        fillBlanksOnly: "true" });
    assert.strictEqual(r.count, 0);
    assert.deepStrictEqual(r.unchangedIds, [{ id: "77" }]);
    assert.strictEqual(r.unchangedCount, 1);
    const links = run("assoc_batch_body.js", { records: r.unchangedIds, toId: 5 });
    assert.deepStrictEqual(JSON.parse(links.body).inputs, [{ from: { id: "77" }, to: { id: "5" } }]);
});

test("mtmc_line_items_body: only Nuance-supplied items, numbers parsed, SKU kept", () => {
    const r = run("mtmc_line_items_body.js", { dealId: 42, currency: "USD", vendor: "Nuance Medical", lineItems: { results: [
        { properties: { name: "Cryodose TA", quantity: "2", price: "$24,000.00", hs_sku: "CTA-1", vendor__name: "Nuance Medical" } },
        { properties: { name: "Other gadget", quantity: "1", price: "10", vendor__name: "Acme Devices" } },
        { properties: { name: "", vendor__name: "Nuance Medical" } }] } });
    assert.strictEqual(r.count, 1);
    assert.strictEqual(r.skippedOtherVendor, 1);
    const item = JSON.parse(r.body).inputs[0];
    assert.deepStrictEqual(item.properties, { name: "Cryodose TA", hs_line_item_currency_code: "USD", quantity: 2, price: 24000, hs_sku: "CTA-1" });
    assert.strictEqual(item.associations[0].to.id, "42");
    assert.strictEqual(run("mtmc_line_items_body.js", { dealId: 42, vendor: "", lineItems: { results: [{ properties: { name: "Other", vendor__name: "Acme" } }] } }).count, 1);
});

test("assoc_batch_body", () => {
    const r = run("assoc_batch_body.js", { records: { status: "COMPLETE", results: [{ id: "1" }, { id: "2" }] }, toId: 9 });
    assert.strictEqual(r.count, 2);
    assert.deepStrictEqual(JSON.parse(r.body).inputs[1], { from: { id: "2" }, to: { id: "9" } });
});

test("notes_for_copy: prefixes, skips echoes, uses author then fallback", () => {
    const r = run("notes_for_copy.js", {
        notes: { results: [
            { id: "n2", properties: { hs_note_body: "<p>Second</p>", hs_timestamp: "2026-10-02T10:00:00Z", hubspot_owner_id: "" } },
            { id: "n1", properties: { hs_note_body: "<div>First &amp; foremost</div>", hs_timestamp: "2026-10-01T10:00:00Z", hubspot_owner_id: "77" } },
            { id: "n3", properties: { hs_note_body: "<p><strong>[Note from MTMC Team. Rep Name: X]</strong></p><p>echo</p>" } },
            { id: "n4", properties: { hs_note_body: "" } }] },
        owners: { results: [{ id: "77", firstName: "Collen", lastName: "<R>" }] },
        label: "Nuance", skipPrefix: "[Note from MTMC Team", fallbackRep: "Deal Owner"
    });
    assert.strictEqual(r.count, 2);
    assert.strictEqual(r.notes[0].id, "n1");                     // oldest first
    assert.ok(r.notes[0].body.startsWith("<p><strong>[Note from Nuance Team. Rep Name: Collen &lt;R&gt;]</strong></p><div>First"));
    assert.ok(r.notes[1].body.includes("Rep Name: Deal Owner]"));
});

test("pick_synced_deal honours link property and pipeline allow-list", () => {
    const deals = { results: [
        { id: "20", properties: { mtmc_deal_id: "555", pipeline: "999", hubspot_owner_id: "1" } },
        { id: "30", properties: { mtmc_deal_id: "", pipeline: "31457678" } },
        { id: "40", properties: { mtmc_deal_id: "556", pipeline: "31457678", hubspot_owner_id: "2" } }] };
    let r = run("pick_synced_deal.js", { deals, linkProperty: "mtmc_deal_id", pipelines: "31457678,915661656" });
    assert.deepStrictEqual(r, { dealId: "40", linkedDealId: "556", dealOwnerId: "2" });
    r = run("pick_synced_deal.js", { deals, linkProperty: "mtmc_deal_id", pipelines: "" });
    assert.strictEqual(r.linkedDealId, "555");
    r = run("pick_synced_deal.js", { deals: { results: [] }, linkProperty: "nuance_deal_id", pipelines: "" });
    assert.strictEqual(r.linkedDealId, null);
});

test("mtmc_update_body: all guide fields, blanks dropped, primary team", () => {
    const r = run("mtmc_update_body.js", {
        deal: { dealname: "Deal A", amount: "48000", closedate: "2026-12-31T00:00:00Z", closed_lost_reason: "",
                distributor_name: "Henry Schein", gpo: "Vizient", source: "Trade show", notes_last_updated: "2026-10-20" },
        owner: { firstName: "Sam", lastName: "Rep", email: "sam@mtmc.com", teams: [{ name: "East", primary: false }, { name: "West", primary: true }] },
        nuanceStage: "", lastActivityProperty: ""
    });
    const p = JSON.parse(r.body).properties;
    assert.strictEqual(p.mtmc_team, "West");   // no ZIP team -> owner's primary team
    assert.strictEqual(p.distributor, "Henry Schein");
    assert.strictEqual(p.gpo, "Vizient");
    assert.strictEqual(p.lead_source, "Trade show");
    assert.strictEqual(p.mtmc_rep_full_name, "Sam Rep");
    assert.ok(!("dealstage" in p) && !("closed_lost_reason" in p) && !("mtmc_last_activity_date" in p));
    const r2 = run("mtmc_update_body.js", { deal: { properties: { notes_last_updated: "2026-10-20", closed_lost_reason: "Budget" } }, owner: {}, nuanceStage: "123", lastActivityProperty: "mtmc_last_activity_date" });
    const p2 = JSON.parse(r2.body).properties;
    const r3 = run("mtmc_update_body.js", { deal: { hubspot_teams_nuance: "Northeast" }, owner: { teams: [{ name: "West", primary: true }] } });
    assert.strictEqual(JSON.parse(r3.body).properties.mtmc_team, "Northeast");   // ZIP team wins
    assert.strictEqual(p2.dealstage, "123");
    assert.strictEqual(p2.closed_lost_reason, "Budget");
    assert.strictEqual(p2.mtmc_last_activity_date, "2026-10-20");
});

console.log(`\n${passed} tests passed`);
