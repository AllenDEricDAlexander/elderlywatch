const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const page = pages.find(p => (p.title || p.name || '').indexOf('06_AUDIO') >= 0);
await eda.dmt_EditorControl.openDocument(page.uuid);
const src = await eda.sys_FileManager.getDocumentSource();
const kinds = {};
for (const line of src.split('\n')) {
    const j = line.indexOf('||');
    if (j < 0) continue;
    let h; try { h = JSON.parse(line.slice(0, j)); } catch (e) { continue; }
    kinds[h.type] = (kinds[h.type] || 0) + 1;
}
return {page: page.title || page.name, uuid: page.uuid, kinds: kinds, head: src.split('\n')[0]};
