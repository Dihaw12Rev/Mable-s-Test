"""Deep links into the HubSpot UI for every asset the audit reports on.

HubSpot changes app URL structure from time to time. Every link the report emits is
built here, so a structure change is a one-file fix rather than a hunt through the
renderers.
"""

from __future__ import annotations

from urllib.parse import quote

APP = "https://app.hubspot.com"

# HubSpot's internal object type IDs, used by the property settings screen.
OBJECT_TYPE_IDS = {
    "contacts": "0-1",
    "companies": "0-2",
    "deals": "0-3",
    "tickets": "0-5",
    "quotes": "0-14",
    "line_items": "0-8",
    "products": "0-7",
    "calls": "0-48",
    "emails": "0-49",
    "meetings": "0-47",
    "notes": "0-4",
    "tasks": "0-27",
}


def workflow(portal_id: str, flow_id: str) -> str:
    return f"{APP}/workflows/{portal_id}/platform/flow/{flow_id}/edit"


def workflows_home(portal_id: str) -> str:
    return f"{APP}/workflows/{portal_id}"


def prop(portal_id: str, object_type: str, name: str) -> str:
    type_id = OBJECT_TYPE_IDS.get(object_type, object_type)
    return (
        f"{APP}/property-settings/{portal_id}/properties"
        f"?type={type_id}&search={quote(name)}"
    )


def form(portal_id: str, form_id: str) -> str:
    return f"{APP}/forms/{portal_id}/editor/{form_id}/edit/form"


def hs_list(portal_id: str, list_id: str) -> str:
    return f"{APP}/contacts/{portal_id}/objectLists/{list_id}"


def marketing_email(portal_id: str, email_id: str) -> str:
    return f"{APP}/email/{portal_id}/edit/{email_id}/edit"


def page(portal_id: str, page_id: str) -> str:
    return f"{APP}/pages/{portal_id}/editor/{page_id}/content"


def blog_post(portal_id: str, post_id: str) -> str:
    return f"{APP}/blog/{portal_id}/edit/{post_id}/content"


def pipeline(portal_id: str, object_type: str) -> str:
    if object_type == "deals":
        return f"{APP}/sales-products-settings/{portal_id}/deals/pipelines"
    return f"{APP}/settings/{portal_id}/objects/{object_type}/pipelines"


def owner(portal_id: str, owner_id: str) -> str:
    return f"{APP}/settings/{portal_id}/users/user/{owner_id}"
