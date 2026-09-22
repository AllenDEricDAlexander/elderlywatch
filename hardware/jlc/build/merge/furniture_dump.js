await eda.dmt_EditorControl.openDocument("f0706db0ae88edcc");
const r = v => (v === undefined || v === null ? null : Math.round(v * 1000) / 1000);
const st = (o, k) => { try { return o[k](); } catch (e) { return 'ERR:' + e.message.slice(0, 40); } };
const rects = [];
for (const q of await eda.sch_PrimitiveRectangle.getAll()) {
    rects.push({
        id: st(q, 'getState_PrimitiveId'),
        box: [r(q.getState_TopLeftX()), r(q.getState_TopLeftY()), r(q.getState_Width()), r(q.getState_Height())],
        color: st(q, 'getState_Color'),
        layer: st(q, 'getState_Layer'),
        visible: st(q, 'getState_Visible'),
        locked: st(q, 'getState_Locked'),
        lineWidth: st(q, 'getState_LineWidth'),
        lineType: st(q, 'getState_LineType'),
        fillStyle: st(q, 'getState_FillStyle'),
        fillColor: st(q, 'getState_FillColor'),
        corner: st(q, 'getState_CornerRadius'),
        rot: st(q, 'getState_Rotation'),
        all: st(q, 'getState'),
    });
}
const texts = [];
for (const t of await eda.sch_PrimitiveText.getAll()) {
    const c = st(t, 'getState_Content');
    if (typeof c === 'string' && (c.indexOf('AIOT-WATCH') === 0 || c.indexOf('电源与充电') === 0 || c.indexOf('发布闸门') >= 0 || c.indexOf('分区框') === 0)) {
        texts.push({id: st(t, 'getState_PrimitiveId'), x: r(t.getState_X()), y: r(t.getState_Y()),
            content: c.slice(0, 40), color: st(t, 'getState_TextColor'), layer: st(t, 'getState_Layer'),
            visible: st(t, 'getState_Visible'), size: st(t, 'getState_FontSize'), align: st(t, 'getState_AlignMode')});
    }
}
return {rectCount: rects.length, textCount: texts.length, rects: rects.slice(0, 4), texts: texts.slice(0, 4)};
