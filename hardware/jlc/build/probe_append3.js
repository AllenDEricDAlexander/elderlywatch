const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const recs = [];
for (const line of src.split('\n')) {
  const i = line.indexOf('||'); if (i < 0) continue;
  recs.push([JSON.parse(line.slice(0, i)), JSON.parse(line.slice(i + 2).replace(/\|$/, ''))]);
}
const attrsOf = {};
for (const [h, b] of recs) if (h.type === 'ATTR') (attrsOf[b.parentId] = attrsOf[b.parentId] || []).push(b);
const numOf = (id) => { const a = (attrsOf[id] || []).find(x => x.key === 'Pin Number'); return a && a.value; };
const tpl = recs.find(([h]) => h.type === 'PIN' && numOf(h.id) === '10');
let ticket = 0, ie = 0;
for (const [h] of recs) { ticket = Math.max(ticket, h.ticket || 0); if (/^ie\d+$/.test(h.id || '')) ie = Math.max(ie, Number(h.id.slice(2))); }
const mk = (type, id, tk, body) => JSON.stringify({type, ticket: tk, id}) + '||' + JSON.stringify(body) + '|';
const build = (withAttrs) => {
  const added = [];
  const pinId = 'ie' + (++ie); const pinTicket = ++ticket;
  const pb = JSON.parse(JSON.stringify(tpl[1])); pb.y = -15; pb.zIndex = ie;
  added.push(mk('PIN', pinId, pinTicket, pb));
  if (withAttrs) for (const a of attrsOf[tpl[0].id] || []) {
    const aid = 'ie' + (++ie); const atk = ++ticket;
    const nb = JSON.parse(JSON.stringify(a));
    nb.parentId = pinId; nb.zIndex = ie;
    if (typeof nb.y === 'number') nb.y = a.y - 165;
    if (a.key === 'Pin Number') nb.value = '21';
    if (a.key === 'Pin Name') nb.value = 'PGND';
    added.push(mk('ATTR', aid, atk, nb));
  }
  return src.replace(/\n$/, '') + '\n' + added.join('\n') + '\n';
};
const out = {};
const withAttrs = build(true);
out.withAttrs = await eda.lib_Symbol.updateDocumentSource(sym, lib, withAttrs);
out.foundWithAttrs = /"value":"21"/.test(await eda.sys_FileManager.getDocumentSource());
if (!out.foundWithAttrs) {
  ticket = 0; ie = 0;
  for (const [h] of recs) { ticket = Math.max(ticket, h.ticket || 0); if (/^ie\d+$/.test(h.id || '')) ie = Math.max(ie, Number(h.id.slice(2))); }
  out.noAttrs = await eda.lib_Symbol.updateDocumentSource(sym, lib, build(false));
  out.foundNoAttrs = /"value":"21"/.test(await eda.sys_FileManager.getDocumentSource());
}
return out;
