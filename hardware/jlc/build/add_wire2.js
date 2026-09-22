const lib = 'ea905f22c789460e8404c7cb6b73ac04', flagDevice = 'ff39f53402a3f08a';
await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const out = {};
const u9 = (await eda.sch_PrimitiveComponent.getAll()).find(c => c.getState_Designator() === 'U9');
const p21 = (await u9.getAllPins()).find(p => p.pinNumber === '21');
const px = p21.x, py = p21.y;
const touches = (l, x, y) => (l[0] === x && l[1] === y) || (l[2] === x && l[3] === y);
out.atPin = (await eda.sch_PrimitiveWire.getAll()).filter(w => touches(w.getState_Line(), px, py)).map(w => ({line: w.getState_Line(), net: w.getState_Net()}));
out.atFlag = (await eda.sch_PrimitiveComponent.getAll()).filter(c => c.getState_X() === 380 && c.getState_Y() === py).map(c => ({id: c.getState_PrimitiveId(), net: c.getState_Net()}));
if (!out.atPin.length) {
  const w = await eda.sch_PrimitiveWire.create([px, py, 380, py], 'GND', null, 1, 0);
  if (!w) throw new Error('wire create returned nothing');
  w.done();
  out.createdWire = true;
}
if (!out.atFlag.length) {
  const f = await eda.sch_PrimitiveComponent.create({libraryUuid: lib, uuid: flagDevice}, 380, py, '1', 180, false, true, true);
  if (!f) throw new Error('flag create returned nothing');
  f.done();
  out.createdFlag = true;
}
out.saved = await eda.sch_Document.save();
out.wiresNow = (await eda.sch_PrimitiveWire.getAll()).filter(w => touches(w.getState_Line(), px, py)).map(w => ({line: w.getState_Line(), net: w.getState_Net()}));
out.flagsNow = (await eda.sch_PrimitiveComponent.getAll()).filter(c => c.getState_X() === 380 && c.getState_Y() === py).map(c => ({id: c.getState_PrimitiveId(), net: c.getState_Net(), name: c.getState_Name(), type: c.getState_ComponentType()}));
return out;
