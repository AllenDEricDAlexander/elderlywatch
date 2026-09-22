await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const w = await eda.sch_PrimitiveWire.create([1400, 1000, 1500, 1000], 'PROBE_A', null, 1, 0);
const names = [];
let proto = w, depth = 0;
while (proto && depth < 5) { names.push(...Object.getOwnPropertyNames(proto)); proto = Object.getPrototypeOf(proto); depth++; }
const out = {wireMethods: [...new Set(names)].filter(n => typeof (w || {})[n] === 'function').sort(),
    hasDone: !!(w && w.done)};
if (w && w.done) w.done();
out.afterDone = (() => { try { return !!w.getState_PrimitiveId(); } catch (e) { return 'ERR'; } })();
const t1 = Date.now();
const saved = await eda.sch_Document.save();
out.saveMs = Date.now() - t1;
out.saved = saved;
const t2 = Date.now();
let second = null, err = null;
try { second = await eda.sch_PrimitiveWire.create([1400, 1020, 1500, 1020], 'PROBE_B', null, 1, 0); } catch (e) { err = String(e && e.message || e).slice(0, 40); }
out.secondAfterSave = second ? second.getState_PrimitiveId() : null;
out.err = err;
if (second && second.done) second.done();
const t3 = Date.now();
let third = null, err3 = null;
try { third = await eda.sch_PrimitiveWire.create([1400, 1040, 1500, 1040], 'PROBE_C', null, 1, 0); } catch (e) { err3 = String(e && e.message || e).slice(0, 40); }
out.thirdWithoutSave = third ? third.getState_PrimitiveId() : null;
out.err3 = err3;
out.save2Ms = Date.now() - t3;
await eda.sch_Document.save();
return out;
