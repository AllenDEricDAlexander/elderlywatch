const PAGE = 'f0706db0ae88edcc';
await eda.dmt_EditorControl.openDocument(PAGE);
const r = v => Math.round(v * 1000) / 1000;
const out = [];
for (const q of await eda.sch_PrimitiveRectangle.getAll()) {
    out.push({id: q.getState_PrimitiveId(), x: r(q.getState_TopLeftX()), y: r(q.getState_TopLeftY()),
        w: r(q.getState_Width()), h: r(q.getState_Height()), rot: q.getState_Rotation(),
        cr: q.getState_CornerRadius(), lw: q.getState_LineWidth(), color: q.getState_Color()});
}
return out;
