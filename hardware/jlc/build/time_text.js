await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const tries = [];
const combos = [
    {x: 200, y: -1200, content: 'A align0 size16', rotation: 0, size: 16, align: 0},
    {x: 200, y: -1240, content: 'B align4 size16', rotation: 0, size: 16, align: 4},
    {x: 200, y: -1280, content: 'C align4 size20 bold', rotation: 0, size: 20, align: 4, bold: true},
    {x: 200, y: -1320, content: 'D align4 size11 source', rotation: 0, size: 11.02362, align: 4}
];
for (const c of combos) {
    let id = null, err = null;
    try {
        const t = await eda.sch_PrimitiveText.create(c.x, c.y, c.content, c.rotation, null, null, c.size, !!c.bold, false, false, c.align);
        id = t ? t.getState_PrimitiveId() : null;
        if (t && t.done) t.done();
    } catch (e) { err = String(e && e.message || e).slice(0, 80); }
    tries.push({combo: c.content, id: id, err: err});
}
await eda.sch_Document.save();
return tries;
