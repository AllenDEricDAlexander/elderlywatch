const r = v => (v === undefined || v === null ? null : Math.round(v * 1000) / 1000);
const parts = [], ports = [], flags = [], wires = [], texts = [], polys = [];
let frame = 0, stubs = 0;
for (const c of await eda.sch_PrimitiveComponent.getAll()) {
    const type = c.getState_ComponentType();
    if (type === 'sheet') { frame++; continue; }
    let net = null;
    try { net = c.getState_Net(); } catch (e) {}
    let name = null;
    try { name = c.getState_Name(); } catch (e) {}
    const rec = {id: c.getState_PrimitiveId(), x: r(c.getState_X()), y: r(c.getState_Y()),
        designator: c.getState_Designator(), name: name, net: net === undefined ? name : (net || name)};
    if (type === 'netport') ports.push(rec);
    else if (type === 'netflag') flags.push(rec);
    else parts.push(rec);
}
for (const w of await eda.sch_PrimitiveWire.getAll()) {
    const line = w.getState_Line();
    if (line[0] === line[2] && line[1] === line[3]) { stubs++; continue; }
    wires.push({id: w.getState_PrimitiveId(), line: line.map(r), net: w.getState_Net()});
}
for (const t of await eda.sch_PrimitiveText.getAll())
    texts.push({id: t.getState_PrimitiveId(), x: r(t.getState_X()), y: r(t.getState_Y()),
        content: t.getState_Content()});
for (const p of await eda.sch_PrimitivePolygon.getAll())
    polys.push({id: p.getState_PrimitiveId(), line: p.getState_Line().map(r)});
return {part: parts.length, port: ports.length, flag: flags.length, wire: wires.length,
    text: texts.length, poly: polys.length, stubs: stubs, frame: frame,
    probeTexts: texts.filter(t => String(t.content).indexOf('WEDGE') >= 0).length};
