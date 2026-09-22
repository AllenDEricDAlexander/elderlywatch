// Probe v2: the align-mode read-back does not match what create() was asked for, so
// measure what actually happens - for each mode, create one text, read its rendered
// box back, and delete it again at the end. Colors round-trip fine (v1: '#FF0000' and
// '#0000FF' came back verbatim; Text has no getState_Color at all).
const PAGE = 'f0706db0ae88edcc';      // 10_ALL
const X = 10000, Y = 9000;
const st = (o, k) => { try { const v = o['getState_' + k](); return v === undefined ? null : v; }
    catch (e) { return null; } };
await eda.dmt_EditorControl.openDocument(PAGE);
const sweep = async () => {
    const t = (await eda.sch_PrimitiveText.getAll()).filter(q => Math.abs(q.getState_X() - X) < 1)
        .map(q => q.getState_PrimitiveId());
    if (t.length) await eda.sch_PrimitiveText.delete(t);
    return t.length;
};
const out = {before: await sweep(), modes: []};
for (const mode of [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]) {
    const y = Y - 400 * (mode + 1);
    const t = await eda.sch_PrimitiveText.create(X, y, '备注CJK-Abc', 0, '#0000FF', null, 30,
        false, false, false, mode);
    if (!t) { out.modes.push({mode: mode, created: false}); continue; }
    const id = t.getState_PrimitiveId();
    const box = await eda.sch_Primitive.getPrimitivesBBox([id]);
    out.modes.push({mode: mode, created: true, readBack: st(t, 'AlignMode'), anchor: [X, y],
        box: box ? [box.minX, box.minY, box.maxX, box.maxY] : null});
}
out.swept = await sweep();
out.saved = await eda.sch_Document.save();
out.textsLeft = (await eda.sch_PrimitiveText.getAll()).length;
return out;
