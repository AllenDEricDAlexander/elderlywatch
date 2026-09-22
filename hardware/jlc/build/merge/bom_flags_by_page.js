const pages = (await eda.dmt_Schematic.getAllSchematicPagesInfo())
    .map(p => ({uuid: p.uuid, name: p.title || p.name || ''}))
    .filter(p => /^\d\d_|10_ALL/.test(p.name));
const rows = [];
const refs = {};
for (const page of pages) {
    await eda.dmt_EditorControl.openDocument(page.uuid);
    const all = await eda.sch_PrimitiveComponent.getAll();
    const parts = all.filter(c => /^[A-Z]+[0-9]+$/.test(c.getState_Designator() || ''));
    let excluded = 0;
    for (const c of parts) {
        const skip = c.getState_AddIntoBom() === false && c.getState_AddIntoPcb() === false;
        if (skip) excluded++;
        const ref = c.getState_Designator();
        refs[ref] = refs[ref] || [];
        if (page.name !== '10_ALL') refs[ref].push(skip ? 'X' : page.name);
    }
    rows.push({page: page.name, parts: parts.length, excluded: excluded});
}
const dupOnSource = Object.entries(refs).filter(([, v]) => v.length !== 1).map(([k, v]) => k + '=' + v.join('+'));
return {rows: rows, sourceRefs: Object.keys(refs).length, refsPerSourcePageOnce: dupOnSource};
