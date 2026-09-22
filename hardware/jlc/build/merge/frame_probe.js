const project = await eda.dmt_Project.getCurrentProjectInfo();
const tab = await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc@' + project.uuid);
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const here = pages.filter(p => p.uuid === 'f0706db0ae88edcc');
const frame = (await eda.sch_PrimitiveComponent.getAll()).find(c => c.getState_ComponentType() === 'sheet');
const keys = frame ? Object.keys(frame).concat(Object.getOwnPropertyNames(Object.getPrototypeOf(frame))) : [];
const states = {};
for (const k of keys) {
    if (!/^getState_/.test(k)) continue;
    try { const v = frame[k](); if (typeof v !== 'function') states[k.replace('getState_', '')] = JSON.stringify(v); } catch (e) {}
}
const content = (await eda.sch_Primitive.getPrimitivesBBox(
    (await eda.sch_PrimitiveComponent.getAll()).filter(c => c.getState_ComponentType() !== 'sheet')
        .map(c => c.getState_PrimitiveId())));
return {pageInfo: here, frameStates: states, contentBBox: content,
    viewport: await eda.dmt_EditorControl.zoomToAllPrimitives(tab)};
