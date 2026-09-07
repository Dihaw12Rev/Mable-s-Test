"""A synthetic portal snapshot shaped like real HubSpot API payloads.

Used to exercise the analyzer and both renderers without touching a live portal.
"""

from __future__ import annotations


def _prop(name, label, obj="contacts", **kw):
    base = {
        "name": name,
        "label": label,
        "type": kw.get("type", "string"),
        "fieldType": kw.get("fieldType", "text"),
        "groupName": kw.get("group", "contactinformation"),
        "hubspotDefined": kw.get("hubspot", False),
        "calculated": kw.get("calculated", False),
        "archived": False,
        "description": kw.get("description", ""),
        "options": kw.get("options", []),
        "createdAt": "2024-02-11T09:00:00Z",
        "updatedAt": "2026-01-04T12:00:00Z",
        "modificationMetadata": {"readOnlyValue": kw.get("read_only", False)},
    }
    return base


def snapshot() -> dict:
    contact_props = [
        _prop("email", "Email", hubspot=True),
        _prop("lifecyclestage", "Lifecycle Stage", hubspot=True, fieldType="select"),
        _prop("hs_lead_status", "Lead Status", hubspot=True, fieldType="select"),
        _prop("hubspot_owner_id", "Contact owner", hubspot=True),
        _prop("jobtitle", "Job Title", hubspot=True),
        _prop("country", "Country", hubspot=True),
        _prop("hs_email_hard_bounce_reason_enum", "Hard bounce reason", hubspot=True, read_only=True),
        _prop("icp_tier", "ICP Tier", group="scoring", fieldType="select"),
        _prop("fit_score", "Fit Score", type="number", fieldType="number", group="scoring"),
        _prop("engagement_score", "Engagement Score", type="number", fieldType="number", group="scoring"),
        _prop("mql_date", "MQL Date", type="datetime", fieldType="date", group="lifecycle"),
        _prop("routing_region", "Routing Region", group="routing", fieldType="select"),
        _prop("suppression_reason", "Suppression Reason", group="compliance"),
        _prop("legacy_sfdc_id", "Legacy SFDC ID", group="integration"),
        _prop("temp_import_flag_2023", "Temp Import Flag 2023", group="integration"),
        _prop("old_campaign_source", "Old Campaign Source", group="integration"),
    ]
    company_props = [
        _prop("name", "Company name", obj="companies", hubspot=True),
        _prop("domain", "Company Domain Name", obj="companies", hubspot=True),
        _prop("industry", "Industry", obj="companies", hubspot=True, fieldType="select"),
        _prop("account_tier", "Account Tier", obj="companies", group="scoring"),
    ]
    deal_props = [
        _prop("dealstage", "Deal Stage", obj="deals", hubspot=True),
        _prop("amount", "Amount", obj="deals", hubspot=True, type="number"),
        _prop("renewal_risk", "Renewal Risk", obj="deals", group="success"),
    ]

    def flow(fid, name, enabled, reads, writes, actions, triggers=None, lists_=None):
        acts = []
        for i, (type_id, prop_name) in enumerate(actions):
            fields = {}
            if prop_name:
                fields = {"property_name": prop_name, "value": {"staticValue": "set"}}
            acts.append({
                "actionId": str(i + 1),
                "type": "SINGLE_CONNECTION",
                "actionTypeId": type_id,
                "actionTypeVersion": 0,
                "fields": fields,
            })
        for r in reads[1:2]:
            acts.append({
                "actionId": "b1",
                "type": "LIST_BRANCH",
                "listBranches": [{"filterBranch": {"filters": [{"property": r, "operation": {"operator": "IS_EQUAL_TO"}}]}}],
            })
        for t in triggers or []:
            acts.append({"actionId": "t", "type": "SINGLE_CONNECTION", "actionTypeId": "0-11",
                         "fields": {"flowId": t}})
        return {
            "id": fid,
            "name": name,
            "isEnabled": enabled,
            "type": "CONTACT_FLOW",
            "objectTypeId": "0-1",
            "revisionId": "12",
            "createdAt": "2025-03-02T10:00:00Z",
            "updatedAt": "2026-06-18T14:30:00Z",
            "_definition_available": True,
            "enrollmentCriteria": {
                "shouldReEnroll": enabled,
                "type": "LIST_BASED",
                "listFilterBranch": {
                    "filterBranches": [{"filters": [{"property": p} for p in reads]}]
                },
            },
            "suppressionListIds": lists_ or [],
            "actions": acts,
        }

    workflows = [
        flow("101", "Lifecycle — MQL promotion", True,
             ["fit_score", "engagement_score"], ["lifecyclestage", "mql_date"],
             [("0-2", "lifecyclestage"), ("0-2", "mql_date"), ("0-1", None), ("0-8", None)],
             triggers=["102"]),
        flow("102", "Lead Routing — territory assignment", True,
             ["routing_region", "country"], ["hubspot_owner_id"],
             [("0-13", "hubspot_owner_id"), ("0-3", None)]),
        flow("103", "Scoring — ICP tier calculation", True,
             ["industry", "jobtitle"], ["icp_tier", "fit_score"],
             [("0-2", "icp_tier"), ("0-2", "fit_score")]),
        flow("104", "Suppression — hard bounce quarantine", True,
             ["hs_email_hard_bounce_reason_enum"], ["suppression_reason", "hs_lead_status"],
             [("0-2", "suppression_reason"), ("0-2", "hs_lead_status"), ("0-5", None)],
             lists_=["9001"]),
        flow("105", "Nurture — welcome sequence", True,
             ["lifecyclestage"], [],
             [("0-4", None), ("0-1", None), ("0-4", None), ("0-99", None)]),
        flow("106", "[TEST] copy of routing v2", False,
             ["routing_region"], ["hubspot_owner_id"],
             [("0-2", "hubspot_owner_id")]),
        flow("107", "Data Hygiene — normalize country", False,
             ["country"], ["country"], [("0-26", None), ("0-2", "country")]),
        flow("108", "Sales — renewal risk alerting", True,
             ["renewal_risk"], [], [("0-3", None), ("0-7", None)]),
    ]

    lists_ = [
        {"listId": "9001", "name": "Suppression — global", "processingType": "DYNAMIC",
         "objectTypeId": "0-1", "updatedAt": "2026-05-01T00:00:00Z",
         "filterBranch": {"filters": [{"property": "suppression_reason"}]}},
        {"listId": "9002", "name": "MQLs — last 90 days", "processingType": "DYNAMIC",
         "objectTypeId": "0-1", "updatedAt": "2026-06-11T00:00:00Z",
         "filterBranch": {"filters": [{"property": "lifecyclestage"}, {"property": "mql_date"}]}},
        {"listId": "9003", "name": "Static — 2024 webinar import", "processingType": "MANUAL",
         "objectTypeId": "0-1", "updatedAt": "2024-09-01T00:00:00Z", "filterBranch": {}},
    ]

    forms = [
        {"id": "f-1", "name": "Request a demo", "formType": "hubspot", "archived": False,
         "createdAt": "2025-01-05T00:00:00Z", "updatedAt": "2026-02-02T00:00:00Z",
         "fieldGroups": [{"fields": [{"name": "email"}, {"name": "jobtitle"}, {"name": "country"}]}]},
        {"id": "f-2", "name": "Newsletter signup", "formType": "hubspot", "archived": False,
         "createdAt": "2024-06-01T00:00:00Z", "updatedAt": "2025-11-20T00:00:00Z",
         "fieldGroups": [{"fields": [{"name": "email"}]}]},
        {"id": "f-3", "name": "Old event form (2023)", "formType": "hubspot", "archived": True,
         "createdAt": "2023-04-01T00:00:00Z", "updatedAt": "2023-08-01T00:00:00Z",
         "fieldGroups": [{"fields": [{"name": "email"}, {"name": "old_campaign_source"}]}]},
    ]

    emails = [
        {"id": "e-1", "name": "Welcome — day 0", "subject": "Welcome aboard",
         "state": "AUTOMATED", "updatedAt": "2026-03-01T00:00:00Z"},
        {"id": "e-2", "name": "Welcome — day 3", "subject": "Getting started",
         "state": "AUTOMATED", "updatedAt": "2026-03-01T00:00:00Z"},
        {"id": "e-3", "name": "Q1 newsletter", "subject": "What's new this quarter",
         "state": "PUBLISHED", "updatedAt": "2026-01-15T00:00:00Z"},
        {"id": "e-4", "name": "Draft — pricing announcement", "subject": "",
         "state": "DRAFT", "updatedAt": "2026-07-02T00:00:00Z"},
    ]

    landing = [
        {"id": "lp-1", "name": "Demo request", "slug": "demo", "url": "https://www.example.com/demo",
         "state": "PUBLISHED", "updatedAt": "2026-04-10T00:00:00Z"},
        {"id": "lp-2", "name": "Webinar — spring 2025", "slug": "webinar-spring-2025",
         "url": "https://www.example.com/webinar-spring-2025", "state": "PUBLISHED",
         "updatedAt": "2025-05-01T00:00:00Z"},
    ]
    site = [
        {"id": "sp-1", "name": "Pricing", "slug": "pricing", "url": "https://www.example.com/pricing",
         "state": "PUBLISHED", "updatedAt": "2026-06-01T00:00:00Z"},
    ]

    return {
        "extracted_at": "2026-08-19T12:00:00+00:00",
        "account": {"portalId": 12345678, "companyName": "Sample Portal",
                    "uiDomain": "app.hubspot.com", "timeZone": "US/Eastern"},
        "owners": [{"id": "1", "email": "rev@example.com", "firstName": "Ada", "lastName": "L"}],
        "schemas": [],
        "properties": {"contacts": contact_props, "companies": company_props, "deals": deal_props},
        "property_groups": {},
        "workflows": workflows,
        "lists": lists_,
        "forms": forms,
        "marketing_emails": emails,
        "landing_pages": landing,
        "site_pages": site,
        "blog_posts": [],
        "pipelines": {"deals": []},
        "skipped": [{"endpoint": "/cms/v3/blogs/posts", "status": 403,
                     "reason": "403 on /cms/v3/blogs/posts: missing content scope"}],
    }
