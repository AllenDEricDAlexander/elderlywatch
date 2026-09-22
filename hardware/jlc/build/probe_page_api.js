await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const out = {};
const wires = await eda.sch_PrimitiveWire.getAll();
out.wireCount = wires.length;
out.wires = wires.slice(0, 3).map(w => { const g = {}; for (const k of ['getState_PrimitiveId','getState_Line','getState_Net']) { try { g[k] = w[k](); } catch (e) { g[k] = 'ERR'; } } return g; });
const comps = await eda.sch_PrimitiveComponent.getAll();
out.compCount = comps.length;
const c0 = comps[0];
const methods = [];
let o = c0;
while (o && o !== Object.prototype) { methods.push(...Object.getOwnPropertyNames(o)); o = Object.getPrototypeOf(o); }
out.compMethods = [...new Set(methods)].filter(k => /^get/.test(k));
const gnd = [];
for (const c of comps) {
  const g = {};
  for (const k of out.compMethods) { try { const v = c[k](); if (v === null || typeof v !== 'object') g[k] = v; } catch (e) {} }
  if (JSON.stringify(g).includes('"GND"')) gnd.push(g);
  if (JSON.stringify(g).includes('"U9"')) out.u9 = g;
}
out.gndSample = gnd.slice(0, 2);
out.gndCount = gnd.length;
return out;
