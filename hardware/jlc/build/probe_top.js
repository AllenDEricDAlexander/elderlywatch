const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const out = [];
for (const p of pages) {
    if ((p.title || p.name || '').indexOf('TOP') < 0 && (p.title || p.name || '') !== 'aiot-watch') continue;
    await eda.dmt_EditorControl.openDocument(p.uuid);
    const comps = await eda.sch_PrimitiveComponent.getAll();
    const texts = (await eda.sch_PrimitiveText.getAll()) || [];
    out.push({page: p.title || p.name, uuid: p.uuid, components: comps.map(c => ({
        desig: c.getState_Designator(), type: c.getState_ComponentType(),
        name: c.getState_Name(), net: c.getState_Net()})),
        texts: texts.map(t => t.getState_Text ? t.getState_Text() : null)});
}
return out;
