const src = await eda.sys_FileManager.getDocumentSource();
const out = [];
for (const l of src.split('\n')) {
  const i = l.indexOf('||');
  if (i < 0) continue;
  let h; try { h = JSON.parse(l.slice(0, i)); } catch (e) { continue; }
  if (h.type === 'WIRE' || h.type === 'LINE') out.push(l);
  if (out.length > 12) break;
}
return out;
