await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const cur = await eda.dmt_SelectControl.getCurrentDocumentInfo();
const src = await eda.sys_FileManager.getDocumentSource();
const lines = (src || '').split('\n');
const heads = new Set();
let pinCount = 0, wireCount = 0;
for (const l of lines) {
  const i = l.indexOf('||');
  if (i < 0) continue;
  try {
    const h = JSON.parse(l.slice(0, i));
    heads.add(h.type);
    if (h.type === 'WIRE') wireCount++;
    if (h.type === 'PIN') pinCount++;
  } catch (e) {}
}
return {doc: cur, length: (src||'').length, lines: lines.length, types: Array.from(heads), wireCount, pinCount, first: lines.slice(0,3)};
