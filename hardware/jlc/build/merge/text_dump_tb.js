const PAGE = 'f0706db0ae88edcc';
await eda.dmt_EditorControl.openDocument(PAGE);
const texts = [];
for (const t of await eda.sch_PrimitiveText.getAll()) {
    texts.push({id: t.getState_PrimitiveId(), x: t.getState_X(), y: t.getState_Y(),
        size: t.getState_FontSize(), align: t.getState_AlignMode(),
        content: t.getState_Content()});
}
// The three widest KiCad-imported captions, so their real extents can be checked against
// the partition frames that now sit next to them.
const ids = texts.map(t => t.id);
const boxes = {};
for (const t of texts.sort((a, b) => (b.content || '').length - (a.content || '').length).slice(0, 3)) {
    boxes[t.content.slice(0, 30)] = await eda.sch_Primitive.getPrimitivesBBox([t.id]);
}
const frames = [];
for (const q of await eda.sch_PrimitiveRectangle.getAll())
    frames.push([q.getState_TopLeftX(), q.getState_TopLeftY(), q.getState_Width(),
        q.getState_Height(), q.getState_LineWidth()]);
return {mine: texts.filter(t => (t.content || '').includes('位号')
    || (t.content || '').includes('图例') || (t.content || '').includes('未选型')),
    widest: boxes, frames: frames};
