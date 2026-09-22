const SCH = 'a27357ea1b21e67b';
const scratch = await eda.dmt_Schematic.createSchematicPage(SCH);
await eda.dmt_EditorControl.openDocument(scratch);
const tries = {save: [], clear: [], bare: []};
let n = 0;
const one = async (bucket, after) => {
    n++;
    const y = 100 * n;
    const t0 = Date.now();
    let id = null, err = null;
    try {
        const w = await eda.sch_PrimitiveWire.create([100, y, 300, y], 'PACE_' + n, null, 1, 0);
        id = w ? w.getState_PrimitiveId() : null;
        if (w && w.done) w.done();
    } catch (e) { err = String(e && e.message || e).slice(0, 30); }
    const t1 = Date.now();
    if (after === 'save') await eda.sch_Document.save();
    if (after === 'clear') { try { eda.sch_SelectControl.clearSelected(); } catch (e) {} }
    tries[bucket].push({y: y, id: id ? 'ok' : 'FAIL', err: err, ms: t1 - t0, afterMs: Date.now() - t1});
};
for (let i = 0; i < 5; i++) await one('save', 'save');
for (let i = 0; i < 5; i++) await one('clear', 'clear');
for (let i = 0; i < 5; i++) await one('bare', null);
const final = await eda.sch_Document.save();
const count = (await eda.sch_PrimitiveWire.getAll()).length;
await eda.dmt_Schematic.deleteSchematicPage(scratch);
return {tries: tries, wiresOnSheet: count, saved: final, deleted: true};
