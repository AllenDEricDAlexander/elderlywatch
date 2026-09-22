await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const PROJ = 'ea905f22c789460e8404c7cb6b73ac04';
const marks = [];
for (let i = 0; i < 4; i++) {
    const t = Date.now();
    const p = await eda.sch_PrimitiveComponent.createNetPort('BI', 'TIMING_NET_' + i, 900 + i * 60, -1100, 180, false);
    const t2 = Date.now();
    if (p) p.done();
    marks.push({netPort: t2 - t, done: Date.now() - t2});
}
for (let i = 0; i < 3; i++) {
    const t = Date.now();
    const c = await eda.sch_PrimitiveComponent.create({libraryUuid: PROJ, uuid: '76eb7c766178926b'}, 900 + i * 200, -1300, '1', 0, false, true, true);
    const t2 = Date.now();
    if (c) { c.done(); }
    const t3 = Date.now();
    await eda.sch_PrimitiveComponent.modify(c.getState_PrimitiveId(), {designator: 'X' + i});
    marks.push({part: t2 - t, done: t3 - t2, modify: Date.now() - t3});
}
marks.push({save: Date.now()});
const t4 = Date.now();
await eda.sch_Document.save();
marks.push({saveMs: Date.now() - t4});
return marks;
