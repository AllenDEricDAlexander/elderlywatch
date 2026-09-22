const tab = await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc@ea905f22c789460e8404c7cb6b73ac04');
const rectId = '34842bd01ddf021d', textId = '4b1cce1b0bbb2688';
const out = {};
out.rectBBox = await eda.sch_Primitive.getPrimitivesBBox([rectId]);
out.textBBox = await eda.sch_Primitive.getPrimitivesBBox([textId]);
const rect = (await eda.sch_PrimitiveRectangle.getAll()).find(x => x.getState_PrimitiveId() === rectId);
out.rectKeys = Object.getOwnPropertyNames(Object.getPrototypeOf(rect)).filter(n => /^get(State|Property)_/.test(n)).join(',');
out.rectState = {};
for (const k of out.rectKeys.split(',')) { try { out.rectState[k.replace(/^get(State|Property)_/, '')] = rect[k](); } catch (e) {} }
const texts = await eda.sch_PrimitiveText.getAll();
const t = texts.find(x => x.getState_PrimitiveId() === textId);
out.textState = {x: t.getState_X(), y: t.getState_Y(), align: t.getState_AlignMode(), size: t.getState_FontSize()};
const variants = [];
for (const a of [0, 1, 2, 3, 4, 5]) {
    const nt = await eda.sch_PrimitiveText.create(5000, -3000, 'ALIGN' + a, 0, null, null, 40, false, false, false, a);
    if (!nt) { variants.push([a, null]); continue; }
    const bb = await eda.sch_Primitive.getPrimitivesBBox([nt.getState_PrimitiveId()]);
    variants.push([a, nt.getState_AlignMode(), bb]);
}
out.alignVariants = variants;
out.saved = await eda.sch_Document.save();
return out;
