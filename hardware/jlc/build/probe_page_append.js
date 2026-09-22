const SCH = 'a27357ea1b21e67b';
const scratch = await eda.dmt_Schematic.createSchematicPage(SCH);
await eda.dmt_EditorControl.openDocument(scratch);
const src = await eda.sys_FileManager.getDocumentSource();
const lines = src.split('\n').filter(l => l.indexOf('||') >= 0);
function parse(text) {
    const out = [];
    for (const line of text.split('\n')) {
        const i = line.indexOf('||');
        if (i < 0) continue;
        try { out.push([JSON.parse(line.slice(0, i)), JSON.parse(line.slice(i + 2).replace(/\|$/, ''))]); } catch (e) {}
    }
    return out;
}
let ticket = 0, ie = 0;
for (const [h] of parse(src)) { ticket = Math.max(ticket, h.ticket || 0); if (/^ie\d+$/.test(h.id || '')) ie = Math.max(ie, Number(h.id.slice(2))); }
const mk = (type, id, tk, body) => JSON.stringify({type, ticket: tk, id}) + '||' + JSON.stringify(body) + '|';
const added = [];
const [wt, wid] = [++ticket, 'ie' + (++ie)];
added.push(mk('WIRE', wid, wt, {zIndex: ie, locked: false}));
const [lt, lid] = [++ticket, 'line' + (++ie)];
added.push(mk('LINE', lid, lt, {startX: 100, startY: 100, endX: 200, endY: 100, lineGroup: wid, color: null, lineWidth: 1, lineType: 0, zIndex: ie, locked: false}));
const [at, aid] = [++ticket, 'ie' + (++ie)];
added.push(mk('ATTR', aid, at, {parentId: wid, key: 'NET', value: 'GND', x: 210, y: 100, visible: false, zIndex: ie}));
const wrote = await eda.sys_FileManager.setDocumentSource(lines.join('\n') + '\n' + added.join('\n'));
const after = parse(await eda.sys_FileManager.getDocumentSource());
const deleted = await eda.dmt_Schematic.deleteSchematicPage(scratch);
return {scratch, before: lines.length, writeReturned: wrote, afterTypes: after.map(r => r[0].type), deleted,
    pagesNow: (await eda.dmt_Schematic.getAllSchematicPagesInfo()).length};
