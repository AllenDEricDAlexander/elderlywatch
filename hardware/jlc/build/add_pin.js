const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const before = await eda.sch_PrimitivePin.getAll();
const existing = before.filter(p => p.getState_PinNumber() === '21');
if (existing.length) return {status: 'ALREADY', ids: existing.map(p => p.getState_PrimitiveId())};
const tpl = before.find(p => p.getState_PinNumber() === '10');
if (!tpl) throw new Error('template pin 10 missing');
const created = await eda.sch_PrimitivePin.create(
  tpl.getState_X(), 15, '21', 'PGND', tpl.getState_Rotation(), tpl.getState_PinLength(), null,
  tpl.getState_PinShape(), 'Power');
if (!created) throw new Error('create returned nothing');
created.done();
const saved = await eda.sch_Document.save();
const after = await eda.sch_PrimitivePin.getAll();
const p21 = after.find(p => p.getState_PinNumber() === '21');
const src = await eda.sys_FileManager.getDocumentSource();
return {status: (saved && p21) ? 'PATCHED' : 'FAILED', saved, count: after.length,
  pin21: p21 ? {id: p21.getState_PrimitiveId(), x: p21.getState_X(), y: p21.getState_Y(), name: p21.getState_PinName(),
    rotation: p21.getState_Rotation(), length: p21.getState_PinLength(), type: p21.getState_pinType(), shape: p21.getState_PinShape()} : null,
  sourceHas21: /"value":"21"/.test(src), sourcePins: (src.match(/"type":"PIN"/g) || []).length};
