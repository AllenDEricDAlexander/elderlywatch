// Probe: which color strings does the client accept, and where does each alignMode
// put the text box? Decoration primitives parked far outside the map, read back, then
// deleted again - the last unknown before merge_schematic_pages.py starts generating
// the border, the partition frames and the remarks. getState_* names differ per
// primitive type, so every read is wrapped (the first run died on Text.getState_Color).
const PAGE = 'f0706db0ae88edcc';      // 10_ALL
const X = 10000, Y = 9000;            // the map lives in 0..6930 x -3800..1453
const st = (o, k) => { try { const v = o['getState_' + k](); return v === undefined ? null : v; }
    catch (e) { return 'ERR:' + k; } };
await eda.dmt_EditorControl.openDocument(PAGE);
const sweep = async () => {
    const r = (await eda.sch_PrimitiveRectangle.getAll()).filter(q => Math.abs(q.getState_TopLeftX() - X) < 1)
        .map(q => q.getState_PrimitiveId());
    const t = (await eda.sch_PrimitiveText.getAll()).filter(q => Math.abs(q.getState_X() - X) < 1)
        .map(q => q.getState_PrimitiveId());
    if (r.length) await eda.sch_PrimitiveRectangle.delete(r);
    if (t.length) await eda.sch_PrimitiveText.delete(t);
    return {rect: r.length, text: t.length};
};
const out = {before: await sweep()};
const rectIds = [], textIds = [];
const rect = await eda.sch_PrimitiveRectangle.create(X, Y, 400, 200, 0, 0, '#FF0000', null, 8, 0, null);
out.rectCreated = !!rect;
if (rect) rectIds.push(rect.getState_PrimitiveId());
for (const mode of [1, 2, 3, 4, 5, 6, 7, 8, 9]) {
    const t = await eda.sch_PrimitiveText.create(X, Y - 400 * mode, '备注CJK-Abc', 0,
        '#0000FF', null, 30, false, false, false, mode);
    out.texts = (out.texts || []);
    out.texts.push([mode, !!t]);
    if (t) textIds.push(t.getState_PrimitiveId());
}
const each = {};
for (const id of rectIds.concat(textIds)) each[id] = await eda.sch_Primitive.getPrimitivesBBox([id]);
out.eachBBox = each;
out.readback = [];
for (const r of await eda.sch_PrimitiveRectangle.getAll()) {
    if (Math.abs(r.getState_TopLeftX() - X) < 1)
        out.readback.push({k: 'rect', color: st(r, 'Color'), fill: st(r, 'FillColor'),
            lw: st(r, 'LineWidth'), lt: st(r, 'LineType'), fs: st(r, 'FillStyle'),
            box: [r.getState_TopLeftX(), r.getState_TopLeftY(), r.getState_Width(), r.getState_Height()]});
}
for (const t of await eda.sch_PrimitiveText.getAll()) {
    if (Math.abs(t.getState_X() - X) < 1)
        out.readback.push({k: 'text', color: st(t, 'Color'), textColor: st(t, 'TextColor'),
            size: st(t, 'FontSize'), align: st(t, 'AlignMode'), content: t.getState_Content(),
            y: t.getState_Y()});
}
out.deleted = {rect: await eda.sch_PrimitiveRectangle.delete(rectIds),
    text: await eda.sch_PrimitiveText.delete(textIds)};
out.after = await sweep();
out.saved = await eda.sch_Document.save();
return out;
