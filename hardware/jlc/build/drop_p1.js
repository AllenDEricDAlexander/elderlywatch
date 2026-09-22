const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const p1 = pages.find(p => (p.title || p.name || '') === 'P1');
if (!p1) return {status: 'NO P1 PAGE', pages: pages.length};
await eda.dmt_EditorControl.openDocument(p1.uuid);
const counts = {comp: (await eda.sch_PrimitiveComponent.getAll()).length, wire: (await eda.sch_PrimitiveWire.getAll()).length};
if (counts.comp || counts.wire) return {status: 'NOT EMPTY, kept', counts: counts};
const deleted = await eda.dmt_Schematic.deleteSchematicPage(p1.uuid);
return {status: 'DELETED', deleted: deleted, pages: (await eda.dmt_Schematic.getAllSchematicPagesInfo()).length};
