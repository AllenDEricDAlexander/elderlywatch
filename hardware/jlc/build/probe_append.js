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
const out = {templateId: tpl[0].id, templateBody: tpl[1], templateAttrs: (attrsOf[tpl[0].id] || []).map(a => a.key + '=' + a.value)};
const mk = (type, id, body) => JSON.stringify({type, ticket, id}) + '||' + JSON.stringify(body) + '|';
const build = (withAttrs) => {
  let t = ticket, n = ie;
  const added = [];
  t++; n++;
  const pb = JSON.parse(JSON.stringify(tpl[1])); pb.y = -15; pb.zIndex = n;
  added.push(mk('PIN', 'ie' + n, pb));
  if (withAttrs) for (const a of attrsOf[tpl[0].id] || []) {
    t++; n++;
    const nb = JSON.parse(JSON.stringify(a)); nb.parentId = 'ie' + n; nb.zIndex = n;
    if (typeof nb.y === 'number') nb.y = a.y - 165;
    if (a.key === 'Pin Number') nb.value = '21';
    if (a.key === 'Pin Name') nb.value = 'PGND';
    added.push(mk('ATTR', 'ie' + n, nb));
  }
  return {text: src.split('\n').join('\n') + '\n' + added.join('\n'), added};
};
const a = build(false);
out.pinOnly = await eda.lib_Symbol.updateDocumentSource(sym, lib, a.text);
out.pinOnlyAdded = a.added;
const b2 = build(true);
out.full = await eda.lib_Symbol.updateDocumentSource(sym, lib, b2.text);
out.fullAdded = b2.added;
const chk = await eda.sys_FileManager.getDocumentSource();
out.nowHas21 = /"value":"21"/.test(chk);
out.lineCount = chk.split('\n').length;
return out;
