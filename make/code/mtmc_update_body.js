// MTMC -> Nuance update: builds the PATCH body for our MTMC Sync deal. Empty values are
// left out so a blank at MTMC (or an unmapped stage) never wipes our data.
const d = (input.deal && (input.deal.properties || input.deal)) || {};
const owner = input.owner || {};
const teams = Array.isArray(owner.teams) ? owner.teams : [];
const ownerTeam = teams.find(t => t.primary) || teams[0] || {};
// MTMC Team: the ZIP-based team MTMC assigned (hubspot_teams_nuance, set by the team-update
// scenarios) wins; the deal owner's primary team is only the fallback, so the two never fight.
const team = { name: clean(d.hubspot_teams_nuance) || clean(ownerTeam.name) };
const props = {
    dealname: d.dealname,
    amount: d.amount,
    closedate: d.closedate,
    dealstage: input.nuanceStage,
    closed_lost_reason: d.closed_lost_reason,
    distributor: d.distributor_name,
    gpo: d.gpo,
    lead_source: d.source,
    mtmc_rep_full_name: [clean(owner.firstName), clean(owner.lastName)].filter(Boolean).join(" "),
    mtmc_rep_email: owner.email,
    mtmc_team: team.name,
    last_synced_at: String(Date.now())
};
// Optional: MTMC's last activity date. Create the Nuance deal property first, then set
// input.lastActivityProperty to its internal name (e.g. mtmc_last_activity_date).
if (clean(input.lastActivityProperty)) props[clean(input.lastActivityProperty)] = d.notes_last_updated;
const properties = {};
for (const [k, v] of Object.entries(props)) if (clean(v)) properties[k] = clean(v);
return { body: JSON.stringify({ properties }), fieldCount: Object.keys(properties).length };
