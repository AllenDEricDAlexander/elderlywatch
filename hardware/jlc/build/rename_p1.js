const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const p1 = pages.find(p => (p.title || p.name || '') === 'P1');
const ok = await eda.dmt_Schematic.modifySchematicPageName(p1.uuid, '10_ALL');
return {renamed: ok, now: (await eda.dmt_Schematic.getAllSchematicPagesInfo()).map(p => [p.uuid, p.name || p.title])};
