const schs = await eda.dmt_Schematic.getAllSchematicsInfo();
const root = schs.find(s => (s.name || s.friendlyName || '').indexOf('aiot') >= 0) || schs[0];
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const mine = pages.filter(p => p.parentSchematicUuid === root.uuid);
const created = await eda.dmt_Schematic.createSchematicPage(root.uuid);
const after = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const fresh = after.find(p => p.uuid === created);
return {rootSchematic: {uuid: root.uuid, name: root.name || root.friendlyName},
    pagesBefore: mine.length, createdUuid: created === undefined ? null : created,
    pagesAfter: (after.filter(p => p.parentSchematicUuid === root.uuid)).length,
    freshInfo: fresh ? {uuid: fresh.uuid, title: fresh.title || fresh.name} : null};
