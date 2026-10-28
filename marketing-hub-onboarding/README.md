# Marketing Hub Onboarding — process design (v2)

The RevGravy Marketing Hub onboarding, step by step, built from the FigJam session and updated with the answers from review. The onboarding runs only in HubSpot Work, and the customer sees it through Supered.

Nothing here has been built in the HubSpot portal. These are design files and a prompt.

## Files

| File | What it is |
|---|---|
| `hubspot-work-prompt.txt` | The exact prompt to paste into HubSpot Work. It builds structure only: template project, sections, tasks, subtasks, board, views, requests table, portfolio |
| `hubspot-work-prompt.md` | How to use the prompt, plus the prompt itself |
| `Marketing_Hub_Onboarding_Process.xlsx` | The sheet: Decisions, Roadmap, Task Template (Program length input compresses dates), Progress Measures, Requests, After the Program, Intake Form, Tech Setup, Training, Comms, HubSpot Work Setup, Tool Fit |
| `roadmap.html` | Visual roadmap for review, with a 60/75/90-day switch |
| `process_data.py` | Single source of truth for all content |
| `build_workbook.py`, `build_roadmap.py`, `build_prompt.py` | Regenerate the sheet, the roadmap and the prompt from `process_data.py` |

To change the process, edit `process_data.py`, then run:

```bash
python3 build_workbook.py && python3 build_roadmap.py && python3 build_prompt.py
```

## What the review decided

- **Program length:** 60–90 days. The plan is laid out for 90. For shorter programs, week one stays fixed and later due dates compress in proportion.
- **Tiers:** Marketing Hub Professional and Enterprise. Setup items are tagged "Pro & Ent" or "Ent only".
- **Roles:** Phil leads strategy through the sale and the handoff, and picks the Architect based on capacity. The Architect takes over after that. Phil comes back for the "what's next" call.
- **Where it lives:**
  - HubSpot Work holds everything internal.
  - Supered holds everything the customer sees.
  - Projects pipelines, tickets, the customer portal and Trello are not used for onboarding.
- **Progress measures:** 0.1, 1.1, 1.2 and 1.3 for every customer. 1.0 and 2.1 only when bought.
- **Requests:** $250 per request, with urgency classes Critical, High, Standard and Not now.
- **Migrations and website work:** in scope, with suggested limits.
- **After the program:** 6 months of free KPI monitoring, then the paid offers.

Questions still open are on the Decisions tab.
