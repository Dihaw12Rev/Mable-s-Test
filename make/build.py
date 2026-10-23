#!/usr/bin/env python3
"""Builds the fixed MTMC <> Nuance Make.com blueprints.

Reads the original exports in make/original/, reuses their native HubSpot modules
(so connection labels and field metadata survive), injects the JavaScript in
make/code/, and writes importable blueprints to make/dist/.

    python3 make/build.py
"""
import copy
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ORIG = ROOT / "original"
CODE = ROOT / "code"
DIST = ROOT / "dist"

# ---------------------------------------------------------------- constants
NUANCE = 9735744                    # Make connection: Nuance HubSpot
MTMC = 9423792                      # Make connection: MTMC HubSpot
CONN_LABEL = {NUANCE: "Nuance HubSpot (admin@revgravy.com)", MTMC: "MTMC HubSpot (admin@revgravy.com)"}

DS_WATERMARKS = (114187, "sync_watermarks")                   # existing: key -> last_run_at (text, epoch ms)
DS_STAGE_MAP = (118696, "Deal Stage Mapping (MTMC <> Nuance)")  # existing: key = MTMC stage ID -> "Nuanca Deal ID"
DS_NOTE_MAP = (138595, "Nuance <> MTMC - Notes Sync")          # needs the v2 structure (see README)

NUANCE_CRYODOSE_PIPELINE = "31457678"
NUANCE_READY_FOR_MTMC = "260719393"
NUANCE_MTMC_SYNC_PIPELINE = "915661656"
NUANCE_MTMC_SYNC_DEFAULT_STAGE = "1394921518"
MTMC_NUANCE_PIPELINE = "866607494"
MTMC_STARTED_DISCOVERY = "1296904839"
MTMC_NUANCE_SUPPLIER_ID = "47591994658"
MTMC_SUPPLIER_OBJECT = "2-56805751"
MTMC_CRYODOSE_TA_PRODUCT = "42895084420"
# Deals that entered "Ready for MTMC" before this date are never auto-sent (prevents a
# flood of old deals on the first run). Move it earlier to backfill on purpose.
HANDOFF_CUTOFF = "2026-10-23T00:00:00.000Z"

HELPERS = (CODE / "_helpers.js").read_text()


# ---------------------------------------------------------------- loading
def load(name):
    return json.loads((ORIG / name).read_text())


def index(flow, out=None):
    out = {} if out is None else out
    for m in flow:
        out[m["id"]] = m
        for r in m.get("routes", []):
            index(r["flow"], out)
        for b in m.get("branches", []):
            index(b["flow"], out)
        index(m.get("onerror") or [], out)
    return out


SRC = {
    "deal_out": index(load("1_nuance_deal_to_mtmc.blueprint.json")["flow"]),
    "deal_in": index(load("2_mtmc_deal_create_to_nuance.blueprint.json")["flow"]),
    "update_in": index(load("3_mtmc_deal_update_to_nuance.blueprint.json")["flow"]),
    "notes_in": index(load("4_mtmc_notes_to_nuance.blueprint.json")["flow"]),
}


def reuse(src, mid, new_id=None, name=None, conn=None):
    """Deep-copies an original module, dropping its old filter/error handler."""
    m = copy.deepcopy(SRC[src][mid])
    m.pop("filter", None)
    m.pop("onerror", None)
    m["id"] = new_id or mid
    md = m.setdefault("metadata", {})
    md.setdefault("designer", {})
    if name:
        md["designer"]["name"] = name
    if conn:
        set_conn(m, conn)
    return m


def set_conn(m, conn):
    m["parameters"]["__IMTCONN__"] = conn
    r = m["metadata"].setdefault("restore", {}).setdefault("parameters", {})
    r["__IMTCONN__"] = {"data": {"scoped": "true", "connection": "hubspotcrm"}, "label": CONN_LABEL[conn]}


# ---------------------------------------------------------------- builders
def filt(name, *conds):
    return {"name": name, "conditions": [[{k: v for k, v in c.items() if v is not None} for c in conds]]}


def cond(a, o, b=None):
    return {"a": a, "o": o, "b": b}


def api(mid, conn, method, url, name, body=None, qs=None, filter=None):
    m = copy.deepcopy(SRC["deal_out"][21])          # a "Make an API call" module as template
    m["id"] = mid
    set_conn(m, conn)
    m["mapper"] = {"url": url, "method": method,
                   "headers": [{"key": "Content-Type", "value": "application/json"}]}
    if body is not None:
        m["mapper"]["body"] = body
    if qs:
        m["mapper"]["qs"] = [{"key": k, "value": v} for k, v in qs]
    m["metadata"]["designer"] = {"name": name}
    m["metadata"]["restore"]["expect"]["method"]["label"] = method
    if filter:
        m["filter"] = filter
    return m


def code(mid, script, inputs, name, filter=None):
    m = copy.deepcopy(SRC["deal_out"][30])          # a Code module as template
    m["id"] = mid
    m["mapper"]["input"] = [{"name": k, "value": v} for k, v in inputs]
    m["mapper"]["codeEditorJavascript"] = HELPERS + "\n" + (CODE / script).read_text()
    m["metadata"]["designer"] = {"name": name}
    m["metadata"]["restore"]["expect"]["input"] = {"items": [None] * len(inputs)}
    if filter:
        m["filter"] = filter
    return m


def feeder(mid, array, name=None):
    return {"id": mid, "module": "builtin:BasicFeeder", "version": 1, "parameters": {},
            "mapper": {"array": array}, "metadata": {"designer": {"name": name} if name else {}}}


def router(mid, *routes):
    return {"id": mid, "module": "builtin:BasicRouter", "version": 1, "mapper": None,
            "metadata": {"designer": {}}, "routes": [{"flow": list(r)} for r in routes]}


def ds_get(mid, store, key, name, filter=None):
    m = {"id": mid, "module": "datastore:GetRecord", "version": 1, "parameters": {"datastore": store[0]},
         "mapper": {"key": key, "returnWrapped": False},
         "metadata": {"designer": {"name": name},
                      "restore": {"parameters": {"datastore": {"label": store[1]}}},
                      "parameters": [{"name": "datastore", "type": "datastore", "label": "Data store", "required": True}],
                      "expect": [{"name": "key", "type": "text", "label": "Key", "required": True},
                                 {"name": "returnWrapped", "type": "boolean", "label": "Return Wrapped Output", "required": True}]}}
    if filter:
        m["filter"] = filter
    return m


def ds_add(mid, store, key, data, name, filter=None):
    m = {"id": mid, "module": "datastore:AddRecord", "version": 1, "parameters": {"datastore": store[0]},
         "mapper": {"key": key, "data": data, "overwrite": True},
         "metadata": {"designer": {"name": name},
                      "restore": {"expect": {"overwrite": {"mode": "chose"}},
                                  "parameters": {"datastore": {"label": store[1]}}},
                      "parameters": [{"name": "datastore", "type": "datastore", "label": "Data store", "required": True}],
                      "expect": [{"name": "key", "type": "text", "label": "Key"},
                                 {"name": "overwrite", "type": "boolean", "label": "Overwrite an existing record", "required": True},
                                 {"name": "data", "type": "collection", "label": "Record",
                                  "spec": [{"name": k, "type": "text", "label": None} for k in data]}]}}
    if filter:
        m["filter"] = filter
    return m


_eid = [9000]


def retry(m, attempts=3, minutes=15):
    """Attach a Break handler: the run is stored as an incomplete execution and retried."""
    _eid[0] += 1
    m["onerror"] = [{"id": _eid[0], "module": "builtin:Break", "version": 1, "parameters": {},
                     "mapper": {"count": str(attempts), "retry": True, "interval": str(minutes)},
                     "metadata": {"designer": {},
                                  "restore": {"expect": {"retry": {"mode": "chose"}}},
                                  "expect": [{"name": "retry", "type": "boolean", "label": "Automatically complete execution", "required": True},
                                             {"name": "count", "type": "integer", "label": "Number of attempts", "required": True},
                                             {"name": "interval", "type": "integer", "label": "Interval between attempts", "required": True}]}}]
    return m


def ignore(m):
    _eid[0] += 1
    m["onerror"] = [{"id": _eid[0], "module": "builtin:Ignore", "version": 1, "parameters": {}, "mapper": {},
                     "metadata": {"designer": {}}}]
    return m


def note_record(origin, nuance_id, mtmc_id, modified):
    return {"origin": origin, "nuance_note_id": nuance_id, "mtmc_note_id": mtmc_id,
            "source_modified_at": modified, "last_synced_at": "{{now}}"}


def create_note(mid, conn, body, timestamp, deal_id, name, filter=None):
    m = reuse("notes_in", 6, mid, name, conn)
    m["mapper"] = {"associations": [{"toId": deal_id, "associationTypeId": 214, "associationCategory": "HUBSPOT_DEFINED"}],
                   "hs_note_body": body, "hs_timestamp": timestamp, "parseCustomFields": True}
    if filter:
        m["filter"] = filter
    return m


def update_note(mid, conn, note_id, body, name, filter=None):
    m = reuse("notes_in", 16, mid, name, conn)
    m["mapper"] = {"noteId": note_id, "hs_note_body": body, "parseCustomFields": True}
    if filter:
        m["filter"] = filter
    return m


# ---------------------------------------------------------------- layout + output
def layout(flow, x, y, st):
    for m in flow:
        d = m.setdefault("metadata", {}).setdefault("designer", {})
        d["x"], d["y"] = x, y
        for e in m.get("onerror") or []:
            e.setdefault("metadata", {}).setdefault("designer", {}).update({"x": x + 150, "y": y + 150})
        for i, r in enumerate(m.get("routes", [])):
            if i:
                st["y"] += 300
            layout(r["flow"], x + 300, y if i == 0 else st["y"], st)
        x += 300


def write(filename, name, flow, instant):
    layout(flow, 0, 0, {"y": 0})
    bp = {"name": name, "flow": flow,
          "metadata": {"instant": instant, "version": 1,
                       "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True, "autoCommitTriggerLast": True,
                                    "sequential": instant, "slots": None, "confidential": False, "dataloss": False,
                                    "dlq": True, "freshVariables": False},
                       "designer": {"orphans": []}, "zone": "us2.make.com", "notes": []}}
    DIST.mkdir(exist_ok=True)
    (DIST / filename).write_text(json.dumps(bp, indent=4, ensure_ascii=False) + "\n")
    return bp


def since(watermark_mid, hours_back, fallback_hours):
    """Epoch-ms lower bound: previous run minus an overlap, or now minus a fallback."""
    return ('{{if(%d.last_run_at; formatDate(addHours(parseDate(%d.last_run_at; "x"); -%d); "x"); '
            'formatDate(addHours(now; -%d); "x"))}}' % (watermark_mid, watermark_mid, hours_back, fallback_hours))


NOTE_FIELDS = "hs_note_body,hs_timestamp,hs_createdate,hs_lastmodifieddate,hubspot_owner_id"


# ================================================================ 1. Nuance deal -> MTMC
def build_deal_out():
    search = reuse("deal_out", 12, name="Cryodose deals to send or update")
    search["mapper"]["limit"] = "200"
    search["mapper"]["filter"] = [
        [  # new handoffs: in Ready for MTMC and never sent (retries any failed handoff automatically)
            {"a": "pipeline", "b": NUANCE_CRYODOSE_PIPELINE, "o": "EQ"},
            {"a": "dealstage", "b": NUANCE_READY_FOR_MTMC, "o": "EQ"},
            {"a": "mtmc_deal_id", "o": "NOT_HAS_PROPERTY"},
            {"a": "hs_v2_date_entered_" + NUANCE_READY_FOR_MTMC, "b": HANDOFF_CUTOFF, "o": "GTE"},
        ],
        [  # edits to deals already sent
            {"a": "pipeline", "b": NUANCE_CRYODOSE_PIPELINE, "o": "EQ"},
            {"a": "mtmc_deal_id", "o": "HAS_PROPERTY"},
            {"a": "hs_lastmodifieddate", "b": since(100, 4, 4), "o": "GT"},
        ],
    ]
    props = search["mapper"]["outputProperties"]
    for p in ("createdate", "pipeline"):
        if p not in props:
            props.append(p)

    owner = api(21, NUANCE, "GET", "/crm/v3/owners/{{12.properties.hubspot_owner_id}}", "Get Nuance deal owner",
                filter=filt("New handoff", cond("{{12.properties.mtmc_deal_id}}", "notexist")))
    mtmc_deal = reuse("deal_out", 18, name="Create deal at MTMC")
    mtmc_deal["mapper"] = json.loads(json.dumps(mtmc_deal["mapper"]).replace("{{13.", "{{12.properties."))
    writeback = retry(reuse("deal_out", 23, name="Write MTMC Deal ID back (prevents duplicates)"))
    writeback["mapper"]["dealId"] = "{{12.id}}"
    line_item = retry(reuse("deal_out", 84, name="Create Cryodose TA line item at MTMC"))
    copy_deal = retry(reuse("deal_out", 64, name="Create linked copy in MTMC Sync"))
    link_back = retry(reuse("deal_out", 65, name="Write Nuance Deal ID on MTMC deal"))
    supplier = retry(reuse("deal_out", 76, name="Associate Nuance Medical supplier"))

    contacts = [
        api(201, NUANCE, "GET", "/crm/v4/objects/deals/{{12.id}}/associations/contacts", "Nuance: deal contacts"),
        code(202, "assoc_to_batch_read.js", [("assoc", "{{201.body}}"), ("properties", "email,firstname,lastname,phone,mobilephone,jobtitle")], "Build contact read"),
        api(203, NUANCE, "POST", "/crm/v3/objects/contacts/batch/read", "Nuance: read contacts", body="{{202.result.body}}",
            filter=filt("Deal has contacts", cond("{{202.result.count}}", "number:greater", "0"))),
        code(204, "contacts_read_by_email_body.js", [("contacts", "{{203.body}}")], "Build MTMC email lookup"),
        api(205, MTMC, "POST", "/crm/v3/objects/contacts/batch/read", "MTMC: find contacts by email", body="{{204.result.body}}"),
        code(206, "nuance_contacts_plan.js", [("contacts", "{{203.body}}"), ("existing", "{{205.body}}"), ("dealId", "{{18.id}}")], "Plan: create new / link existing"),
        router(207,
               [retry(api(208, MTMC, "POST", "/crm/v3/objects/contacts/batch/create", "MTMC: create new contacts (linked to deal)",
                          body="{{206.result.createBody}}", filter=filt("New contacts", cond("{{206.result.createCount}}", "number:greater", "0"))))],
               [retry(api(209, MTMC, "POST", "/crm/v4/associations/contacts/deals/batch/associate/default", "MTMC: link existing contacts",
                          body="{{206.result.associateBody}}", filter=filt("Existing contacts", cond("{{206.result.associateCount}}", "number:greater", "0"))))]),
    ]

    ticket = retry(reuse("deal_out", 77, name="MTMC: Company Creation Request ticket"))
    ticket["filter"] = filt("No company match", cond("{{216.result.matchId}}", "notexist"))
    ticket["mapper"]["subject"] = "Create {{214.result.name}} Company - From Nuance Medical"
    ticket["mapper"]["properties"] = [
        {"key": "company_name", "value": "{{214.result.name}}"},
        {"key": "company_domain_name", "value": "{{214.result.domainUrl}}"},
        {"key": "addre", "value": "{{214.result.address}}"},
        {"key": "city", "value": "{{214.result.city}}"},
        {"key": "zip", "value": "{{214.result.zip}}"},
        {"key": "content", "value": "State: {{214.result.state}}\nCountry: {{214.result.country}}\nNuance company ID: {{212.result.companyId}}\nNuance deal: {{12.properties.dealname}}"},
    ]
    company = [
        api(211, NUANCE, "GET", "/crm/v4/objects/deals/{{12.id}}/associations/companies", "Nuance: deal companies"),
        code(212, "pick_primary_company.js", [("assoc", "{{211.body}}")], "Pick primary company"),
        api(213, NUANCE, "GET", "/crm/v3/objects/companies/{{212.result.companyId}}", "Nuance: read company",
            qs=[("properties", "name,domain,website,address,city,state,zip,country")],
            filter=filt("Deal has a company", cond("{{212.result.count}}", "number:greater", "0"))),
        code(214, "company_search_body.js", [("company", "{{213.body}}")], "Build MTMC company search"),
        api(215, MTMC, "POST", "/crm/v3/objects/companies/search", "MTMC: search by domain / name", body="{{214.result.body}}",
            filter=filt("Has domain or name", cond("{{214.result.hasCriteria}}", "boolean:equal", "true"))),
        code(216, "company_choose_match.js", [("search", "{{215.body}}"), ("domain", "{{214.result.domain}}"), ("name", "{{214.result.name}}")], "Choose one company (domain first)"),
        router(217,
               [retry(api(218, MTMC, "PUT", "/crm/v4/objects/companies/{{216.result.matchId}}/associations/default/deals/{{18.id}}",
                          "MTMC: link matched company", filter=filt("Company matched", cond("{{216.result.matchId}}", "exist"))))],
               [ticket]),
    ]

    notes = [
        api(221, NUANCE, "GET", "/crm/v4/objects/deals/{{12.id}}/associations/notes", "Nuance: deal notes"),
        code(222, "assoc_to_batch_read.js", [("assoc", "{{221.body}}"), ("properties", NOTE_FIELDS)], "Build note read"),
        api(223, NUANCE, "POST", "/crm/v3/objects/notes/batch/read", "Nuance: read notes", body="{{222.result.body}}",
            filter=filt("Deal has notes", cond("{{222.result.count}}", "number:greater", "0"))),
        api(224, NUANCE, "GET", "/crm/v3/owners", "Nuance: owners (for rep names)", qs=[("limit", "500")]),
        code(225, "notes_for_copy.js", [("notes", "{{223.body}}"), ("owners", "{{224.body}}"), ("label", "Nuance"),
                                        ("skipPrefix", "[Note from MTMC Team"), ("fallbackRep", "{{21.body.firstName}} {{21.body.lastName}}")],
             "Prepare notes for MTMC"),
        feeder(226, "{{225.result.notes}}", "Each note"),
        ds_get(227, DS_NOTE_MAP, "nuance:{{226.id}}", "Already synced?"),
        create_note(228, MTMC, "{{226.body}}", "{{226.timestamp}}", "{{18.id}}", "MTMC: create note",
                    filter=filt("Not synced yet", cond("{{227.origin}}", "notexist"))),
        ds_add(229, DS_NOTE_MAP, "nuance:{{226.id}}", note_record("nuance", "{{226.id}}", "{{228.id}}", "{{226.modified}}"), "Remember note (Nuance side)"),
        ds_add(230, DS_NOTE_MAP, "mtmc:{{228.id}}", note_record("nuance", "{{226.id}}", "{{228.id}}", "{{226.modified}}"), "Remember note (MTMC side)"),
    ]

    owner_upd = api(87, NUANCE, "GET", "/crm/v3/owners/{{12.properties.hubspot_owner_id}}", "Get Nuance deal owner",
                    filter=filt("Already sent (update)", cond("{{12.properties.mtmc_deal_id}}", "exist")))
    update = retry(reuse("deal_out", 86, name="Update MTMC deal (no stage / close date)"))

    flow = [
        ds_get(100, DS_WATERMARKS, "nuance_handoff", "Last run"),
        ds_add(101, DS_WATERMARKS, "nuance_handoff", {"last_run_at": '{{formatDate(now; "x")}}'}, "Save this run"),
        search,
        router(10,
               [owner, mtmc_deal, writeback, line_item, copy_deal, link_back, supplier,
                router(200, contacts, company, notes)],
               [owner_upd, update]),
    ]
    return write("1_nuance_deal_to_mtmc_v2.blueprint.json", "Nuance Deal → MTMC (Create + Update) v2", flow, False)


# ================================================================ 2. MTMC new deal -> Nuance
def build_deal_in():
    hook = reuse("deal_in", 2)
    sleep = reuse("deal_in", 3)
    get_deal = ignore(reuse("deal_in", 4, name="MTMC: get deal"))
    get_deal["mapper"]["outputProperties"] = [
        "dealname", "dealstage", "pipeline", "amount", "closedate", "hubspot_owner_id", "distributor_name", "gpo",
        "source", "closed_lost_reason", "supplier_name", "nuance_deal_id", "nuance_last_synced_at", "hs_object_id"]
    supplier = reuse("deal_in", 7, name="MTMC: deal suppliers")
    supplier["filter"] = filt("Not already linked to Nuance (prevents duplicates and echoes of our handoffs)",
                              cond("{{4.properties.nuance_deal_id}}", "notexist"),
                              cond("{{4.properties.nuance_last_synced_at}}", "notexist"))
    owner = reuse("deal_in", 6, name="MTMC: deal owner")
    owner["filter"] = filt("Nuance Medical is a supplier",
                           cond('{{join(map(7.body.results; "toObjectId"); ",")}}', "text:contain", MTMC_NUANCE_SUPPLIER_ID))
    stage = ds_get(36, DS_STAGE_MAP, "{{4.properties.dealstage}}", "Stage mapping")
    create = retry(reuse("deal_in", 14, name="Nuance: create MTMC Sync deal"))
    for p in create["mapper"]["properties"]:
        if p["key"] == "dealstage":
            p["value"] = "{{ifempty(36.`Nuanca Deal ID`; \"%s\")}}" % NUANCE_MTMC_SYNC_DEFAULT_STAGE
        if p["key"] == "mtmc_deal_id":
            p["value"] = "{{4.id}}"
    link = retry(reuse("deal_in", 17, name="MTMC: write Nuance Deal ID (prevents duplicates)"))

    line_items = [
        reuse("deal_in", 8, name="MTMC: deal line items"),
        code(301, "assoc_to_batch_read.js", [("assoc", "{{8.body}}"), ("properties", "name,quantity,price")], "Build line item read"),
        api(302, MTMC, "POST", "/crm/v3/objects/line_items/batch/read", "MTMC: read line items", body="{{301.result.body}}",
            filter=filt("Deal has line items", cond("{{301.result.count}}", "number:greater", "0"))),
        reuse("deal_in", 15, name="Build Nuance line items"),
    ]
    line_items[-1]["mapper"]["input"][0]["value"] = "{{302.body.results}}"
    li_create = retry(reuse("deal_in", 16, name="Nuance: create line items"))
    li_create["filter"] = filt("Has line items", cond("{{15.result.count}}", "number:greater", "0"))
    line_items.append(li_create)

    contacts = [
        reuse("deal_in", 12, name="MTMC: deal contacts"),
        code(311, "assoc_to_batch_read.js", [("assoc", "{{12.body}}"), ("properties", "email,firstname,lastname,phone,jobtitle")], "Build contact read"),
        api(312, MTMC, "POST", "/crm/v3/objects/contacts/batch/read", "MTMC: read contacts", body="{{311.result.body}}",
            filter=filt("Deal has contacts", cond("{{311.result.count}}", "number:greater", "0"))),
        code(313, "contacts_read_by_email_body.js", [("contacts", "{{312.body}}"), ("properties", "email,firstname,lastname,phone,jobtitle")], "Build Nuance email lookup"),
        api(314, NUANCE, "POST", "/crm/v3/objects/contacts/batch/read", "Nuance: existing contacts by email", body="{{313.result.body}}"),
        code(315, "mtmc_contacts_upsert_body.js", [("contacts", "{{312.body}}"), ("existing", "{{314.body}}"), ("fillBlanksOnly", "false")],
             "Build upsert (match by email)"),
        retry(api(316, NUANCE, "POST", "/crm/v3/objects/contacts/batch/upsert", "Nuance: create / update contacts", body="{{315.result.body}}",
                  filter=filt("Contacts with email", cond("{{315.result.count}}", "number:greater", "0")))),
        code(317, "assoc_batch_body.js", [("records", "{{316.body}}"), ("toId", "{{14.id}}")], "Build contact links"),
        retry(api(318, NUANCE, "POST", "/crm/v4/associations/contacts/deals/batch/associate/default", "Nuance: link contacts to deal",
                  body="{{317.result.body}}", filter=filt("Has contacts", cond("{{317.result.count}}", "number:greater", "0")))),
    ]

    company = [
        reuse("deal_in", 13, name="MTMC: deal companies"),
        code(321, "pick_primary_company.js", [("assoc", "{{13.body}}")], "Pick primary company"),
        api(322, MTMC, "GET", "/crm/v3/objects/companies/{{321.result.companyId}}", "MTMC: read company",
            qs=[("properties", "name,domain,website")],
            filter=filt("Deal has a company", cond("{{321.result.count}}", "number:greater", "0"))),
        code(323, "company_search_body.js", [("company", "{{322.body}}")], "Build Nuance company search"),
        api(324, NUANCE, "POST", "/crm/v3/objects/companies/search", "Nuance: search by domain / name", body="{{323.result.body}}",
            filter=filt("Has domain or name", cond("{{323.result.hasCriteria}}", "boolean:equal", "true"))),
        code(325, "company_choose_match.js", [("search", "{{324.body}}"), ("domain", "{{323.result.domain}}"), ("name", "{{323.result.name}}")],
             "Choose one company (domain first, then exact name)"),
        router(326,
               [retry(api(327, NUANCE, "PUT", "/crm/v4/objects/companies/{{325.result.matchId}}/associations/default/deals/{{14.id}}",
                          "Nuance: link matched company", filter=filt("Company matched", cond("{{325.result.matchId}}", "exist"))))],
               [retry(api(328, NUANCE, "POST", "/crm/v3/objects/companies", "Nuance: create company (name + domain)",
                          body="{{323.result.createBody}}", filter=filt("No match", cond("{{325.result.matchId}}", "notexist")))),
                retry(api(329, NUANCE, "PUT", "/crm/v4/objects/companies/{{328.body.id}}/associations/default/deals/{{14.id}}",
                          "Nuance: link new company"))]),
    ]

    notes = [
        api(331, MTMC, "GET", "/crm/v4/objects/deals/{{4.id}}/associations/notes", "MTMC: deal notes"),
        code(332, "assoc_to_batch_read.js", [("assoc", "{{331.body}}"), ("properties", NOTE_FIELDS)], "Build note read"),
        api(333, MTMC, "POST", "/crm/v3/objects/notes/batch/read", "MTMC: read notes", body="{{332.result.body}}",
            filter=filt("Deal has notes", cond("{{332.result.count}}", "number:greater", "0"))),
        api(334, MTMC, "GET", "/crm/v3/owners", "MTMC: owners (for rep names)", qs=[("limit", "500")]),
        code(335, "notes_for_copy.js", [("notes", "{{333.body}}"), ("owners", "{{334.body}}"), ("label", "MTMC"),
                                        ("skipPrefix", "[Note from Nuance Team"), ("fallbackRep", "{{6.body.firstName}} {{6.body.lastName}}")],
             "Prepare notes for Nuance"),
        feeder(336, "{{335.result.notes}}", "Each note"),
        ds_get(337, DS_NOTE_MAP, "mtmc:{{336.id}}", "Already synced?"),
        create_note(338, NUANCE, "{{336.body}}", "{{336.timestamp}}", "{{14.id}}", "Nuance: create note",
                    filter=filt("Not synced yet", cond("{{337.origin}}", "notexist"))),
        ds_add(339, DS_NOTE_MAP, "mtmc:{{336.id}}", note_record("mtmc", "{{338.id}}", "{{336.id}}", "{{336.modified}}"), "Remember note (MTMC side)"),
        ds_add(340, DS_NOTE_MAP, "nuance:{{338.id}}", note_record("mtmc", "{{338.id}}", "{{336.id}}", "{{336.modified}}"), "Remember note (Nuance side)"),
    ]

    flow = [hook, sleep, get_deal, supplier, owner, stage, create, link, router(300, line_items, contacts, company, notes)]
    return write("2_mtmc_deal_create_to_nuance_v2.blueprint.json", "MTMC New Deal → Nuance (Create) v2", flow, True)


# ================================================================ 3. MTMC deal update -> Nuance
def build_update_in():
    hook = reuse("update_in", 37)
    get_deal = reuse("update_in", 38, name="MTMC: get deal")
    get_deal["mapper"]["outputProperties"] = [
        "dealname", "dealstage", "amount", "closedate", "hubspot_owner_id", "distributor_name", "gpo", "source",
        "closed_lost_reason", "notes_last_updated", "nuance_deal_id", "hs_object_id"]
    owner = reuse("update_in", 40, name="MTMC: deal owner")
    owner["filter"] = filt("Linked to a Nuance deal", cond("{{38.properties.nuance_deal_id}}", "exist"))
    stage = ds_get(36, DS_STAGE_MAP, "{{38.properties.dealstage}}", "Stage mapping")
    body = code(401, "mtmc_update_body.js", [("deal", "{{38.properties}}"), ("owner", "{{40.body}}"), ("nuanceStage", "{{36.`Nuanca Deal ID`}}"),
                                             ("lastActivityProperty", "")], "Build update (skips blanks)")
    patch = retry(api(402, NUANCE, "PATCH", "/crm/v3/objects/deals/{{38.properties.nuance_deal_id}}", "Nuance: update MTMC Sync deal",
                      body="{{401.result.body}}"))
    return write("3_mtmc_deal_update_to_nuance_v2.blueprint.json", "MTMC Deal Updated → Nuance (Update) v2",
                 [hook, get_deal, owner, stage, body, patch], True)


# ================================================================ 4/5. Notes (both directions)
def build_notes(src_conn, dst_conn, src_label, other_label, link_prop, pipelines, watermark_key, filename, title):
    """Scans notes created OR edited since the last run in the source portal and mirrors them.

    src_label is the team that wrote the note; other_label's copies are skipped (loop guard).
    The note map stores both directions so copies are never echoed back.
    """
    src_key = "nuance" if src_conn == NUANCE else "mtmc"
    dst_key = "mtmc" if src_key == "nuance" else "nuance"
    search = reuse("notes_in", 2, name=f"{src_label}: notes created or edited since last run", conn=src_conn)
    search["mapper"]["limit"] = "1000"
    search["mapper"]["direction"] = "ASCENDING"
    search["mapper"]["propertyName"] = "hs_lastmodifieddate"
    search["mapper"]["filter"] = [[{"a": "hs_lastmodifieddate", "b": since(500, 1, 1), "o": "GT"}]]

    assoc = reuse("notes_in", 7, name="Note's deals", conn=src_conn)
    assoc["filter"] = filt("Not a copy from the other portal",
                           cond("{{2.properties.hs_body_preview}}", "text:notstartwith", f"[Note from {other_label} Team"))
    assoc["mapper"]["limit"] = "50"

    def rep_lookup(mid):
        return api(mid, src_conn, "GET", "/crm/v3/owners/{{ifempty(2.properties.hubspot_owner_id; 512.result.dealOwnerId)}}",
                   f"{src_label}: note author")

    body = f"<p><strong>[Note from {src_label} Team. Rep Name: {{{{%d.body.firstName}}}} {{{{%d.body.lastName}}}}]</strong></p>{{{{2.properties.hs_note_body}}}}"
    src_id_field = f"{src_key}_note_id"
    dst_id_field = f"{dst_key}_note_id"

    def rec(dst_id):
        r = {"origin": src_key, src_id_field: "{{2.id}}", dst_id_field: dst_id,
             "source_modified_at": "{{2.properties.hs_lastmodifieddate}}", "last_synced_at": "{{now}}"}
        return {k: r[k] for k in ("origin", "nuance_note_id", "mtmc_note_id", "source_modified_at", "last_synced_at")}

    create_route = [
        rep_lookup(13),
        create_note(6, dst_conn, body % (13, 13), "{{2.properties.hs_timestamp}}", "{{512.result.linkedDealId}}", f"{other_label}: create note"),
        ds_add(14, DS_NOTE_MAP, f"{src_key}:{{{{2.id}}}}", rec("{{6.id}}"), f"Remember note ({src_label} side)"),
        ds_add(15, DS_NOTE_MAP, f"{dst_key}:{{{{6.id}}}}", rec("{{6.id}}"), f"Remember note ({other_label} side)"),
    ]
    create_route[0]["filter"] = filt("New note", cond("{{3.origin}}", "notexist"))
    retry(create_route[1])

    update_route = [
        rep_lookup(17),
        retry(update_note(16, dst_conn, "{{3.%s}}" % dst_id_field, body % (17, 17), f"{other_label}: update note")),
        ds_add(18, DS_NOTE_MAP, f"{src_key}:{{{{2.id}}}}", rec("{{3.%s}}" % dst_id_field), "Save edit time"),
    ]
    update_route[0]["filter"] = filt("Edited since last sync (and written here)",
                                     cond("{{3.origin}}", "text:equal", src_key),
                                     cond("{{2.properties.hs_lastmodifieddate}}", "date:greater", "{{3.source_modified_at}}"))

    flow = [
        ds_get(500, DS_WATERMARKS, watermark_key, "Last run"),
        ds_add(501, DS_WATERMARKS, watermark_key, {"last_run_at": '{{formatDate(now; "x")}}'}, "Save this run"),
        search,
        assoc,
        code(510, "assoc_to_batch_read.js", [("assoc", "{{7.associations.deals}}"), ("properties", f"{link_prop},hubspot_owner_id,pipeline")],
             "Build deal read"),
        api(511, src_conn, "POST", "/crm/v3/objects/deals/batch/read", "Read note's deals", body="{{510.result.body}}",
            filter=filt("Note is on a deal", cond("{{510.result.count}}", "number:greater", "0"))),
        code(512, "pick_synced_deal.js", [("deals", "{{511.body}}"), ("linkProperty", link_prop), ("pipelines", pipelines)],
             "Pick the synced deal"),
        ds_get(3, DS_NOTE_MAP, f"{src_key}:{{{{2.id}}}}", "Already synced?",
               filter=filt("Deal is synced", cond("{{512.result.linkedDealId}}", "exist"))),
        router(5, create_route, update_route),
    ]
    return write(filename, title, flow, False)


if __name__ == "__main__":
    build_deal_out()
    build_deal_in()
    build_update_in()
    for args in [
        (MTMC, NUANCE, "MTMC", "Nuance", "nuance_deal_id", "", "mtmc_notes",
         "4_mtmc_notes_to_nuance_v2.blueprint.json", "MTMC Notes → Nuance (Create + Update) v2"),
        (NUANCE, MTMC, "Nuance", "MTMC", "mtmc_deal_id", f"{NUANCE_CRYODOSE_PIPELINE},{NUANCE_MTMC_SYNC_PIPELINE}", "nuance_notes",
         "5_nuance_notes_to_mtmc_v2.blueprint.json", "Nuance Notes → MTMC (Create + Update) v2"),
    ]:
        build_notes(*args)
    print("\n".join(sorted(p.name for p in DIST.glob("*.json"))))
