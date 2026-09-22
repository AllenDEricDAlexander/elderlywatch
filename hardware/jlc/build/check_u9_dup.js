await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const comps = await eda.sch_PrimitiveComponent.getAll();
const u9 = comps.find(c => c.getState_Designator() === 'U9');
const tip = (await u9.getAllPins()).find(p => String(p.pinNumber) === '21');
const near = (x, y) => Math.abs(x) < 40 && Math.abs(y) < 40;
const ports = comps.filter(c => c.getState_ComponentType() === 'netport'
    && near(c.getState_X() - tip.x, c.getState_Y() - tip.y))
    .map(c => ({id: c.getState_PrimitiveId(), net: c.getState_Net(),
        x: c.getState_X(), y: c.getState_Y()}));
const wires = (await eda.sch_PrimitiveWire.getAll()).filter(w => {
    const l = w.getState_Line();
    return near(l[0] - tip.x, l[1] - tip.y) || near(l[2] - tip.x, l[3] - tip.y);
}).map(w => ({line: w.getState_Line(), net: w.getState_Net()}));
return {tip: {x: tip.x, y: tip.y}, ports: ports, wires: wires};
