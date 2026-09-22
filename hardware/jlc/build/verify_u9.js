await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const src = await eda.sys_FileManager.getDocumentSource();
const recs = [];
for (const line of src.split('\n')) {
  const i = line.indexOf('||'); if (i < 0) continue;
  try { recs.push([JSON.parse(line.slice(0, i)), JSON.parse(line.slice(i + 2).replace(/\|$/, ''))]); } catch (e) {}
}
const line = recs.find(([h, b]) => h.type === 'LINE' && b.startX === 490 && b.startY === 215 && b.endX === 380 && b.endY === 215);
const group = line ? recs.find(([h]) => h.type === 'WIRE' && h.id === line[1].lineGroup) : null;
const net = group ? recs.find(([h, b]) => h.type === 'ATTR' && b.parentId === group[0].id && b.key === 'NET') : null;
const flag = recs.find(([h, b]) => h.type === 'COMPONENT' && b.x === 380 && b.y === 215);
const flagAttrs = flag ? Object.fromEntries(recs.filter(([h, b]) => h.type === 'ATTR' && b.parentId === flag[0].id).map(([, b]) => [b.key, b.value])) : null;
const comps = await eda.sch_PrimitiveComponent.getAll();
const u9 = comps.find(c => c.getState_Designator() === 'U9');
const p21 = (await u9.getAllPins()).find(p => p.pinNumber === '21');
const flagObj = comps.find(c => c.getState_X() === 380 && c.getState_Y() === -215);
return {
  wire: line ? {id: line[0].id, group: line[1].lineGroup, net: net ? net[1].value : null} : null,
  flag: flag ? {id: flag[0].id, device: flagAttrs.Device, symbol: flagAttrs.Symbol, name: flagAttrs.Name} : null,
  flagApi: flagObj ? {net: flagObj.getState_Net(), type: flagObj.getState_ComponentType()} : null,
  pin21: p21 ? {x: p21.x, y: p21.y, name: p21.pinName, type: p21.pinType} : null,
  pinCount: (await u9.getAllPins()).length,
  totalWires: recs.filter(([h]) => h.type === 'WIRE').length
};
