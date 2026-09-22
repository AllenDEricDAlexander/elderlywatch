// Paint-probe: do RECTANGLE primitives render at all on 10_ALL?
// The sheet furniture is in the model (12 rects, correct colour/width, and they even widen
// zoomToAllPrimitives' bbox) but no #FF9900 pixel appears in the render. This drops one bright
// rect, one polygon outline and one text into the empty head band so a render can say which
// primitive type the client refuses to paint.  mode=delete sweeps them back out.
const MODE = "__MODE__";
const tab = await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
await eda.dmt_EditorControl.activateDocument(tab);
const MARK = 'PROBE_PAINT_XYZ';
const near = (a, b) => Math.abs(a - b) < 1;
if (MODE === 'delete') {
    const gone = {rect: 0, poly: 0, text: 0};
    for (const q of await eda.sch_PrimitiveRectangle.getAll()) {
        if (near(q.getState_TopLeftX(), 900) && near(q.getState_TopLeftY(), 1750)) {
            await eda.sch_PrimitiveRectangle.delete(q.getState_PrimitiveId());
            gone.rect++;
        }
    }
    for (const p of await eda.sch_PrimitivePolygon.getAll()) {
        const l = p.getState_Line();
        if (near(l[0], 2500) && near(l[1], 1750)) {
            await eda.sch_PrimitivePolygon.delete(p.getState_PrimitiveId());
            gone.poly++;
        }
    }
    for (const t of await eda.sch_PrimitiveText.getAll()) {
        if (String(t.getState_Content()).indexOf(MARK) === 0) {
            await eda.sch_PrimitiveText.delete(t.getState_PrimitiveId());
            gone.text++;
        }
    }
    await eda.sch_Document.save();
    return {gone: gone, rects: (await eda.sch_PrimitiveRectangle.getAll()).length};
}
const made = {};
const r = await eda.sch_PrimitiveRectangle.create(900, 1750, 400, 120, 0, 0, '#FF9900', null, 10, 0, null);
made.rect = r ? r.getState_PrimitiveId() : 'falsy';
made.rectNow = (await eda.sch_PrimitiveRectangle.getAll()).length;
const polyPts = [2500, 1750, 2900, 1750, 2900, 1630, 2500, 1630, 2500, 1750];
const p = await eda.sch_PrimitivePolygon.create(polyPts, '#0066FF', null, 10, 0);
made.poly = p ? p.getState_PrimitiveId() : 'falsy';
made.polyNow = (await eda.sch_PrimitivePolygon.getAll()).length;
const t = await eda.sch_PrimitiveText.create(4200, 1700, MARK, 0, '#CC00FF', null, 60, false, false, false, 1);
made.text = t ? t.getState_PrimitiveId() : 'falsy';
made.textNow = (await eda.sch_PrimitiveText.getAll()).length;
await eda.sch_Document.save();
return {tab: tab, made: made};
