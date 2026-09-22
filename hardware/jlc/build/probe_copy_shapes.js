const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const page = pages.find(p => (p.title || p.name || '').indexOf('05_DISPLAY') >= 0);
await eda.dmt_EditorControl.openDocument(page.uuid);
function dump(o) {
    const seen = {}, out = {};
    let proto = o, depth = 0;
    while (proto && depth < 4) {
        for (const k of Object.getOwnPropertyNames(proto)) {
            if (k.indexOf('getState_') === 0 && !(k in seen)) {
                try { seen[k] = true; out[k.slice(9)] = o[k](); } catch (e) { seen[k] = 'ERR'; }
            }
        }
        proto = Object.getPrototypeOf(proto); depth++;
    }
    return out;
}
const src = await eda.sys_FileManager.getDocumentSource();
const polys = [];
for (const line of src.split('\n')) {
    const j = line.indexOf('||');
    if (j < 0) continue;
    let h; try { h = JSON.parse(line.slice(0, j)); } catch (e) { continue; }
    if (h.type === 'POLY') polys.push(line.slice(0, 260));
}
const comps = await eda.sch_PrimitiveComponent.getAll();
const wires = await eda.sch_PrimitiveWire.getAll();
const texts = await eda.sch_PrimitiveText.getAll();
return {page: page.title || page.name, counts: {comps: comps.length, wires: wires.length,
    texts: texts.length, polys: polys.length},
    compPart: dump(comps.find(c => /^[A-Z]+[0-9]+$/.test(c.getState_Designator() || ''))),
    compPort: dump(comps.find(c => c.getState_ComponentType() === 'netport')),
    wire: dump(wires[0]), text: dump(texts[0]), polys: polys.slice(0, 3)};
