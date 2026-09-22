const page='35d0bca337813128';
await eda.dmt_EditorControl.openDocument(page);
function dump(o) {
    const seen = {}, out = {};
    let proto = o, depth = 0;
    while (proto && depth < 4) {
        for (const k of Object.getOwnPropertyNames(proto)) {
            if (k.indexOf('getState_') === 0 && !(k in seen)) {
                try { seen[k] = true; const v = o[k](); if (typeof v === 'object' || typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') out[k.slice(9)] = v; } catch (e) { seen[k] = true; }
            }
        }
        proto = Object.getPrototypeOf(proto); depth++;
    }
    return out;
}
const comps=await eda.sch_PrimitiveComponent.getAll();
const ids=comps.map(c=>c.getState_PrimitiveId());
const bb=await eda.sch_Primitive.getPrimitivesBBox(ids);
const polys=await eda.sch_PrimitivePolygon.getAll();
const wires=await eda.sch_PrimitiveWire.getAll();
return {count:{comps:comps.length,polys:polys.length,wires:wires.length},
    bboxType: typeof bb, bbox: bb,
    compSample: [dump(comps.find(c=>/^[A-Z]+[0-9]+$/.test(c.getState_Designator()||''))), dump(comps.find(c=>c.getState_ComponentType()==='netport'))],
    polySample: dump(polys[0]), wireSample: dump(wires[0])};
