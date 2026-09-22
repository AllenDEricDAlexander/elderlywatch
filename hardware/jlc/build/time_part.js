const t0 = Date.now();
await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const PROJ = 'ea905f22c789460e8404c7cb6b73ac04';
const out = {tried: []};
for (const lib of [PROJ, '']) {
    const t1 = Date.now();
    let c = null, err = null;
    try { c = await eda.sch_PrimitiveComponent.create({libraryUuid: lib, uuid: '76eb7c766178926b'}, 1100, -900, '1', 0, false, true, true); }
    catch (e) { err = String(e && e.message || e).slice(0, 120); }
    out.tried.push({lib: lib, ms: Date.now() - t1, err: err, id: c ? c.getState_PrimitiveId() : null,
        desig: c ? (() => { try { return c.getState_Designator(); } catch (e) { return 'ERR'; } })() : null});
    if (c) break;
}
out.saved = await eda.sch_Document.save();
out.total = Date.now() - t0;
return out;
