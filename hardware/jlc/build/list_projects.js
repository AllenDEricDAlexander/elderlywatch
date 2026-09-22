const out = {errors: [], projects: []};
let teams = [];
try { teams = await eda.dmt_Team.getAllTeamsInfo(); } catch (e) { out.errors.push('teams: ' + e.message); }
const seen = new Set();
for (const team of teams || []) {
  let uuids = [];
  try { uuids = await eda.dmt_Project.getAllProjectsUuid(team.uuid); } catch (e) { out.errors.push('list ' + team.name + ': ' + e.message); continue; }
  for (const u of uuids || []) {
    if (seen.has(u)) continue; seen.add(u);
    let i = null;
    try { i = await eda.dmt_Project.getProjectInfo(u); } catch (e) { out.errors.push('info ' + u + ': ' + e.message); }
    out.projects.push({uuid: u, name: (i && (i.friendlyName || i.name)) || '?', team: team.name});
  }
}
out.currentProject = (await eda.dmt_Project.getCurrentProjectInfo())?.friendlyName;
return out;
