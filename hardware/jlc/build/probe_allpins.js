await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const comps = await eda.sch_PrimitiveComponent.getAll();
const u9 = comps.find(c => c.getState_Designator() === 'U9');
const pins = await u9.getAllPins();
return {count: pins.length, sample: pins.slice(0, 4), all: pins.map(p => [p.pinNumber || p.number || p.name, p.net || p.netName]).slice(9)};
