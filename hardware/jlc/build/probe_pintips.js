const out = {};
for (const [tag, page] of [['source_05', '35d0bca337813128'], ['merged_10_ALL', 'f0706db0ae88edcc']]) {
    await eda.dmt_EditorControl.openDocument(page);
    const rows = [];
    for (const c of await eda.sch_PrimitiveComponent.getAll()) {
        let type = '';
        try { type = c.getState_ComponentType(); } catch (e) {}
        if (type !== 'netport') continue;
        let pins = [];
        try { pins = await c.getAllPins(); } catch (e) { pins = 'ERR'; }
        rows.push({net: c.getState_Net(), at: [c.getState_X(), c.getState_Y()],
            symbol: (c.getState_Symbol() || {}).name,
            pins: pins === 'ERR' ? pins : pins.map(p => [p.x, p.y, p.pinNumber])});
    }
    out[tag] = rows.sort((a, b) => a.at[1] - b.at[1]);
}
return out;
