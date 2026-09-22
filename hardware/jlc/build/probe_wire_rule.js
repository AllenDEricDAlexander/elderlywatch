await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const tries = [];
const attempt = async (x1, y1, x2, y2, net) => {
    let id = null, err = null;
    try {
        const w = await eda.sch_PrimitiveWire.create([x1, y1, x2, y2], net, null, 1, 0);
        id = w ? w.getState_PrimitiveId() : null;
        if (w && w.done) w.done();
    } catch (e) { err = String(e && e.message || e).slice(0, 40); }
    tries.push({net: net, y: y1, id: id, err: err});
};
for (const [i, y] of [1000, 1015, 1030, 1045].entries()) await attempt(600, y, 700, y, 'PAR_' + i);
for (const [i, y] of [1100, 1115, 1130].entries()) await attempt(800, y, 900, y, 'SAME');
for (const [i, y] of [1200, 1220, 1235].entries()) await attempt(600, y, 700, y, 'MIX_' + i);
await eda.sch_Document.save();
return tries;
