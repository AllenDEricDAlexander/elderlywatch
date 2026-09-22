const t0 = Date.now();
await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const marks = {open: Date.now() - t0};
const t1 = Date.now();
let c = null, err = null;
try { c = await eda.sch_PrimitiveComponent.create({libraryUuid: '', uuid: '86a999c80b83faa1'}, 700, -500, '1', 180, false, true, true); }
catch (e) { err = String(e && e.message || e).slice(0, 200); }
marks.createMs = Date.now() - t1;
marks.err = err;
marks.id = c ? c.getState_PrimitiveId() : null;
marks.type = c ? (() => { try { return c.getState_ComponentType(); } catch (e) { return 'ERR'; } })() : null;
return marks;
