const tab = await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc@ea905f22c789460e8404c7cb6b73ac04');
const out = {tab: tab};
const t = await eda.sch_PrimitiveText.create(3500, -2000, '分区备注：电源与充电 / 未选型 D01', 0, null, null, 10, true, false, false, 4);
out.textId = t ? t.getState_PrimitiveId() : null;
const r = await eda.sch_PrimitiveRectangle.create(3400, -2100, 900, 400, 0, 0, null, null, 3, 0, 0);
out.rectId = r ? r.getState_PrimitiveId() : null;
out.saved = await eda.sch_Document.save();
const texts = await eda.sch_PrimitiveText.getAll();
const back = texts.find(x => x.getState_PrimitiveId() === out.textId);
out.text = back ? [back.getState_Content(), back.getState_FontSize(), back.getState_Bold(), back.getState_AlignMode()] : null;
const rects = await eda.sch_PrimitiveRectangle.getAll();
const rb = rects.find(x => x.getState_PrimitiveId() === out.rectId);
out.rect = rb ? Object.fromEntries(['X','Y','Width','Height','LineType','LineWidth','FillColor','Color','CornerRadius','PrimitiveType'].map(k => {
    try { return [k, rb['getState_' + k] ? rb['getState_' + k]() : null]; } catch (e) { return [k, 'ERR']; }
})) : null;
out.rectCount = rects.length;
out.bbox = await eda.sch_Primitive.getPrimitivesBBox([out.textId, out.rectId].filter(Boolean));
return out;
