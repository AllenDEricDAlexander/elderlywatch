await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const comps = await eda.sch_PrimitiveComponent.getAll();
const kinds = {};
for (const c of comps) {
    const d = c.getState_Designator() || '';
    if (/^[A-Z]+[0-9]+$/.test(d)) continue;
    const key = JSON.stringify([d, c.getState_Name(), c.getState_Net(), c.getState_ComponentType()]);
    kinds[key] = (kinds[key] || 0) + 1;
}
return Object.entries(kinds).map(([k, n]) => ({n, designator_name_net_type: JSON.parse(k)}));
