const page='35d0bca337813128';
await eda.dmt_EditorControl.openDocument(page);
const comps=await eda.sch_PrimitiveComponent.getAll();
const out=[];
for (const c of comps) {
    const rec={};
    for (const k of ['PrimitiveId','ComponentType','Designator','Name','Net','X','Y','Rotation','Mirror','SubPartName','AddIntoBom','AddIntoPcb']) {
        try { rec[k]=c['getState_'+k](); } catch(e) { rec[k]='ERR:'+String(e).slice(0,40); }
    }
    try { rec.Component=c.getState_Component(); } catch(e){ rec.Component='ERR'; }
    out.push(rec);
}
return out;
