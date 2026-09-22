await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const out = [];
for (const [x, y, tag] of [[0, 387.56, 'exact cell edge'], [60, 387.56, 'inset 60'], [60, 380, 'inset 60 round']]) {
    let id = null, err = null;
    try {
        const t = await eda.sch_PrimitiveText.create(x, y, '05_DISPLAY', 0, null, null, 16, true, false, false, 0);
        id = t ? t.getState_PrimitiveId() : null;
        if (t && t.done) t.done();
    } catch (e) { err = String(e && e.message || e).slice(0, 80); }
    out.push({tag: tag, x: x, y: y, id: id, err: err});
}
await eda.sch_Document.save();
return out;
