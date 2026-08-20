# SKU-based line item creation (MTMC → HOM)

## What changed

Previously the scenario copied MTMC line items to HOM as **free-form** line items:
only `name`, `price`, `quantity` and currency were sent, with no link to HOM's
product library. The HOM deal ended up with text-only lines that don't roll up
to a product, so HOM couldn't report on what was actually being sold.

Line items are now matched to the **HOM product library by SKU**. A matched line
item is created against the HOM product (`hs_product_id`), exactly as if a rep
had picked it from the HOM product picker.

## Flow

```
10 Aggregator (MTMC line items)
   ↓
13 HubSpot (HOM) > Create a Deal
   ↓
60 Build HOM Product SKU Search      ← new (Code)
   ↓
61 HubSpot (HOM) > Find Products by SKU  ← new (Search API)
   ↓
16 Match SKUs & Build Line Items     ← rewritten (Code)
   ↓
15 Line Item Associations            (batch create, unchanged)
```

One extra HTTP call per run, regardless of how many line items the deal has.

### Module 9 — Get Line Item's Supplier
`hs_sku` and `hs_product_id` added to the output properties, so the SKU is
available downstream. MTMC line items already carry `hs_product_id`, i.e. they
are created from MTMC's product library, so `hs_sku` is populated.

### Module 60 — Build HOM Product SKU Search
Collects the **distinct** SKUs across the deal's line items (trimmed,
case-insensitive dedup) and builds one HubSpot search body.

### Module 61 — Find Products by SKU
`POST /crm/v3/objects/products/search` on the **HOM** connection, filtering
`hs_sku IN [...]`.

### Module 16 — Match SKUs & Build Line Items
Indexes the returned HOM products by normalised SKU and builds the batch-create
body, setting `hs_product_id` on every match.

## Behaviour decisions

These are set as constants at the top of module 16 and are one-line changes:

| Constant | Default | Meaning |
|---|---|---|
| `PRICE_SOURCE` | `"mtmc"` | Carry the MTMC unit price across. Keeps the HOM line items consistent with the deal `amount`, which is also copied from MTMC. Set to `"hom"` to price off the HOM catalog instead. |
| `NAME_SOURCE` | `"hom"` | Name the line item after the HOM product, so HOM's catalog naming wins. Set to `"mtmc"` to keep the MTMC name. |
| `CREATE_UNMATCHED` | `true` | Create a SKU with no HOM product as a free-form line item (the old behaviour), so the deal total stays correct. Set to `false` to drop it. |

`description` is only carried over from MTMC for **unmatched** lines — a matched
line inherits the description from the HOM product.

## Matching rules

- SKUs are compared trimmed and case-insensitively (` ps-6800 ` matches `PS-6800`).
- If the HOM catalog has two products with the same SKU, the first wins and
  `duplicateSkuCount` reports it.
- A deal with no line items (or no SKUs) sends a sentinel SKU that matches
  nothing, so the search never receives an empty `IN` list — HubSpot rejects
  those with a 400, which would stop the scenario before the company/contact
  branches run.

## Reporting

Module 16 returns, alongside `bodyString`:

- `matchedCount` / `unmatchedCount`
- `unmatched` — array of `{ sku, name, mtmcLineItemId }`
- `unmatchedSummary` — ready-to-send text block
- `duplicateSkuCount`

Nothing consumes these yet. To get alerted when a SKU is missing from the HOM
catalog, add a router branch after module 16 filtered on
`{{16.result.unmatchedCount}} > 0` and map `{{16.result.unmatchedSummary}}` into
a Slack/email module.

## Known limits

- HubSpot's search API allows **100 values** in an `IN` filter. A deal with more
  than 100 distinct SKUs would truncate; module 60 reports the excess as
  `overflowCount`. Not currently handled, since deals are far below that.
- Search results are capped at `limit: 100`, which matches the filter cap.

## Editing the code modules

`blueprints/src/*.js` are the readable sources for the two Code modules. They
are embedded into the blueprint JSON as the `codeEditorJavascript` field. Edit
the source, then re-embed — keep the two in sync.

## Fix: aggregator source module (module 10)

Module 10's **Source Module** was set to module 9 ("Get a Line Item") instead of
module 6 (the Iterator). This is pre-existing and unrelated to SKU matching, but
it caps every run at one line item.

The aggregator groups bundles by the *cycle* of its source module. Module 9 is a
1-in/1-out action, so each of its bundles closed a group on its own: three line
items produced three groups of one, rather than one group of three. Everything
downstream of the aggregator — including **Create a Deal** — then ran once per
line item.

Source Module must be the module that multiplies bundles, i.e. the Iterator (6).

Any test run made before this fix will have produced one HOM deal per line item;
the extras need deleting.
