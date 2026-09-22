const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const recs = [];
for (const line of src.split('\n')) {
  const i = line.indexOf('||'); if (i < 0) continue;
  recs.push([JSON.parse(line.slice(0, i)), JSON.parse(line.slice(i + 2).replace(/\|$/, '')), line]);
}
const out = {};
const write = async (label, text) => { out[label] = await eda.lib_Symbol.updateDocumentSource(sym, lib, text); };
const body = recs[recs.length - 1][2].replace(/\|$/, '');
const head = JSON.parse(recs[recs.length - 1][0] ? JSON.stringify(recs[recs.length - 1][0]) : '{}');
out.control = await write('control', src);
const dupAttr = JSON.parse(JSON.stringify(recs[recs.length - 1][1]));
dupAttr.value = 'EXTRA';
const extra = JSON.stringify({type: 'ATTR', ticket: head.ticket + 1, id: 'ie900'}) + '||' + JSON.stringify(dupAttr) + '|';
out.appendAttr = await write('appendAttr', src.replace(/\n$/, '') + '\n' + extra + '\n');
out.stillThere = (await eda.sys_FileManager.getDocumentSource()).includes('EXTRA');
return out;
