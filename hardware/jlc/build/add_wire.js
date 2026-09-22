const lib = 'ea905f22c789460e8404c7cb6b73ac04', flagDevice = 'ff39f53402a3f08a';
await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const out = {};
const comps = await eda.sch_PrimitiveComponent.getAll();
const u9 = comps.find(c => c.getState_Designator() === 'U9');
const pins = await u9.getAllPins();
const p21 = pins.find(p => p.pinNumber === '21');
out.pin21Before = {x: p21.x, y: p21.y, noConnected: p21.noConnected};
const wires = await eda.sch_PrimitiveWire.getAll();
out.wireThere = wires.some(w => { const l = w.getState_Line(); return l[1] === p21.y && l[3] === p21.y; });
const flags = comps.filter(c => c.getState_Y() === p21.y);
out.flagThere = flags.length > 0;
if (!out.wireThere) {
  const w = await eda.sch_PrimitiveWire.create([p21.x, p21.y, 380, p21.y], 'GND', null, 1, 0);
  if (!w) throw new Error('wire create returned nothing');
  w.done();
}
if (!out.flagThere) {
  const f = await eda.sch_PrimitiveComponent.create({libraryUuid: lib, uuid: flagDevice}, 380, p21.y, '1', 180, false, true, true);
  if (!f) throw new Error('flag create returned nothing');
  f.done();
}
out.saved = await eda.sch_Document.save();
const after = await (await eda.sch_PrimitiveComponent.getAll()).find(c => c.getState_Designator() === 'U9').getAllPins();
const q = after.find(p => p.pinNumber === '21');
out.pin21After = {x: q.x, y: q.y, noConnected: q.noConnected};
out.netOfWire = (await eda.sch_PrimitiveWire.getAll()).find(w => { const l = w.getState_Line(); return l[1] === q.y; });
out.wireNet = out.netOfWire ? out.netOfWire.getState_Net() : null;
delete out.netOfWire;
const cs = await eda.sch_PrimitiveComponent.getAll();
const at = cs.find(c => c.getState_Y() === q.y && c.getState_X() === 380);
out.flag = at ? {id: at.getState_PrimitiveId(), net: at.getState_Net(), name: at.getState_Name(), type: at.getState_ComponentType()} : null;
return out;
