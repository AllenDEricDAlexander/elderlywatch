await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const src = await eda.sys_FileManager.getDocumentSource();
const hits = src.split('\n').filter(l => l.includes('"y":215') || l.includes('215,"'));
const wires = await eda.sch_PrimitiveWire.getAll();
const near = wires.map(w => w.getState_Line()).filter(l => l[1] === -215 || l[3] === -215);
return {sourceHits: hits.slice(0, 10), wireCount: wires.length, near, lines215: src.split('\n').filter(l => /"startY":215|"endY":215/.test(l))};
