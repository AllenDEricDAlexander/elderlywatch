const lib = 'ea905f22c789460e8404c7cb6b73ac04';
const sym = '7ac0f6329abd612c';
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const pins = {}, order = [];
for (const line of src.split('\n')) {
    const i = line.indexOf('||');
    if (i < 0) continue;
    let h, b;
    try { h = JSON.parse(line.slice(0, i)); b = JSON.parse(line.slice(i + 2).replace(/\|$/, '')); }
    catch (e) { continue; }
    if (h.type === 'PIN') { pins[h.id] = Object.assign({}, b); order.push(h.id); }
    if (h.type === 'ATTR' && pins[b.parentId]) {
        const map = pins[b.parentId];
        if (b.key === 'Pin Number') map.num = b.value;
        if (b.key === 'Pin Name') map.nm = b.value;
        if (b.key === 'Pin Type') map.ty = b.value;
    }
}
return order.map(id => { const p = pins[id];
    return {num: p.num, nm: p.nm, x: p.positionX, y: p.positionY, len: p.length, rot: p.rotation}; });
