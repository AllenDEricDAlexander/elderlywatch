const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const page = pages.find(p => (p.title || p.name || '').indexOf('06_AUDIO') >= 0);
await eda.dmt_EditorControl.openDocument(page.uuid);
const comps = await eda.sch_PrimitiveComponent.getAll();
const g = comps.filter(c => c.getState_Net() === 'GND');
const one = g[0];
const seen = {};
let proto = one, depth = 0;
while (proto && depth < 4) {
    for (const k of Object.getOwnPropertyNames(proto)) {
        if (k.indexOf('getState_') === 0 && !(k in seen)) {
            try { seen[k] = one[k](); } catch (e) { seen[k] = 'ERR'; }
        }
    }
    proto = Object.getPrototypeOf(proto); depth++;
}
return {pageUuid: page.uuid, gndPorts: g.length, getters: seen};
