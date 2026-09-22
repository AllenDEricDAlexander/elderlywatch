await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const comps=await eda.sch_PrimitiveComponent.getAll();
const wires=await eda.sch_PrimitiveWire.getAll();
const texts=await eda.sch_PrimitiveText.getAll();
const polys=await eda.sch_PrimitivePolygon.getAll();
return {comps: comps.map(c=>[c.getState_PrimitiveId(), c.getState_ComponentType(), c.getState_Designator(), c.getState_Name(), c.getState_Net(), c.getState_X(), c.getState_Y()]),
    wires: wires.map(w=>[w.getState_PrimitiveId(), w.getState_Line(), w.getState_Net()]),
    texts: texts.map(t=>[t.getState_PrimitiveId(), t.getState_X(), t.getState_Y(), t.getState_Content()]),
    polys: polys.length};
