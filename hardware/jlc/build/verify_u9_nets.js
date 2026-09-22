await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const u9 = (await eda.sch_PrimitiveComponent.getAll()).find(c => c.getState_Designator() === 'U9');
const wires = await eda.sch_PrimitiveWire.getAll();
const out = [];
for (const p of await u9.getAllPins()) {
  const exact = [], loose = [];
  for (const w of wires) {
    const l = w.getState_Line();
    const d = Math.min(Math.hypot(l[0] - p.x, l[1] - p.y), Math.hypot(l[2] - p.x, l[3] - p.y));
    if (d === 0) exact.push(w.getState_Net());
    else if (d < 0.01) loose.push({net: w.getState_Net(), off: d});
  }
  out.push({pin: p.pinNumber, name: p.pinName, x: p.x, y: p.y, exact: [...new Set(exact)], loose});
}
return out;
