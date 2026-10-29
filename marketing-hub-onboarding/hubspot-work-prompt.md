# HubSpot Work prompts: client onboarding

All of these are generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

## How tasks get created

The Task Library holds 99 tasks: 58 Core tasks every customer gets once, plus one module per hub (Marketing Hub 16, Sales Hub 14, Service Hub 11). Ops sets **Products purchased** on the customer's row and ticks **Create tasks**. The Onboarding Task Generator agent copies Core plus the matching modules into the shared Customer Task table, and records them in **Tasks created for**, so ticking it again later only adds new hubs.

All customers share one Customer Task table instead of having a project each, because HubSpot Work agents can't reach into per-customer projects. Filter any view by Customer to see one customer.

## For the workspace you already have, in this order

| Step | File | What it does |
|---|---|---|
| 1 | `hubspot-work-library-1-restructure.txt` | Turns the Marketing Hub template into the Task Library: Module column, MH- IDs, hub-neutral Core tasks. |
| 2 | `hubspot-work-library-2-sales-hub.txt` | Adds the Sales Hub module (14 tasks). |
| 3 | `hubspot-work-library-3-service-hub.txt` | Adds the Service Hub module (11 tasks). |
| 4 | `hubspot-work-library-4-customers.txt` | Adds Products purchased, Create tasks and Tasks created for to Customers, and Module to Customer Task. |
| 5 | `hubspot-work-agent-prompts.md` | Create (or replace) the Onboarding Task Generator agent with prompt #1. The other agents are unchanged. |

Paste steps 1–4 into the workspace chat one at a time, approving each plan. Test with your next real customer before turning the agents on.

## Building from scratch

`hubspot-work-prompt.txt` builds the whole workspace (library with all three hubs, plus the Onboarding Portfolio tables) in a new workspace. Then create the agents.
