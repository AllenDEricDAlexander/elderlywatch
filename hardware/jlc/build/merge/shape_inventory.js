const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const out = [];
for (const p of pages) {
    await eda.dmt_EditorControl.openDocument(p.uuid);
    out.push({name: p.title || p.name || p.friendlyName || '',
        rects: (await eda.sch_PrimitiveRectangle.getAll()).length,
        polys: (await eda.sch_PrimitivePolygon.getAll()).length,
        arcs: (await eda.sch_PrimitiveArc.getAll()).length});
}
return out;
