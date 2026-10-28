# Marketing Hub Onboarding — process design (draft v1)

The RevGravy Marketing Hub onboarding, step by step, built from the FigJam session. It covers what happens after the sale: tasks, what we ask the customer, technical setup, training, communications, and where each piece should live in HubSpot.

Nothing here has been built in the HubSpot portal. These are design files for review.

## Files

| File | What it is |
|---|---|
| `Marketing_Hub_Onboarding_Process.xlsx` | The sheet: Roadmap, Task Template (77 tasks), Intake Form, Tech Setup, Training, Comms, Tool Fit, HubSpot Build Spec, Open Questions |
| `roadmap.html` | Visual roadmap for review (timeline, tool recommendation, filterable tasks, open questions) |
| `hubspot-work-prompt.md` | Ready-to-paste prompt that has HubSpot Work build the workspace (tables, forms, docs, agents) |
| `process_data.py` | Single source of truth for all content |
| `build_workbook.py`, `build_roadmap.py` | Regenerate the sheet and the roadmap from `process_data.py` |

To change the process, edit `process_data.py`, then run:

```bash
python3 build_workbook.py && python3 build_roadmap.py
```

## Recommendation: Work vs Projects vs Tickets

The three tools do different jobs, so the recommendation is to use them together:

- **HubSpot Work:** the team's operating hub. It holds the template library, intake form, onboarding tracker, playbook docs and AI agents (handoff brief, weekly update drafts, delay alerts). It's in public beta, so start it as a pilot.
- **Projects object:** one onboarding record per customer, associated to the deal. It gives tasks, Gantt, health tracking and customer-portal visibility. The Factories (progress measures) already live here.
- **Tickets:** client requests during the program: urgency class, $250 out-of-scope requests and "not now" ideas. Keep using the existing *Active* pipeline.
- **Tasks:** every to-do gets an owner and a due date, so it lands on the Architect's queue and calendar.

## Key assumptions (see the Open Questions tab)

- The program runs 90 days. Day 0 is when the deal reaches *Start Payment Received*.
- Phil is the strategy lead and an Architect is assigned per customer.
- Supered is the client-facing layer, and Trello is retired.
