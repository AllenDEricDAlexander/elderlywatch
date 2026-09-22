const lib = 'ea905f22c789460e8404c7cb6b73ac04';
const sym = '7ac0f6329abd612c';
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const want = {Designator: -48, Value: -36};
const lines = src.split('\n');
let hits = 0;
for (let i = 0; i < lines.length; i++) {
    const j = lines[i].indexOf('||');
    if (j < 0) continue;
    let h, b;
    try { h = JSON.parse(lines[i].slice(0, j)); b = JSON.parse(lines[i].slice(j + 2).replace(/\|$/, '')); }
    catch (e) { continue; }
    if (h.type !== 'ATTR' || !(b.key in want) || b.parentId !== '1') continue;
    if (!lines[i].endsWith('|')) continue;
    b.y = want[b.key];
    lines[i] = lines[i].slice(0, j) + '||' + JSON.stringify(b) + '|';
    hits++;
}
if (hits !== 2) throw new Error('expected 2 ATTR lines, rewrote ' + hits);
const ok = await eda.lib_Symbol.updateDocumentSource(sym, lib, lines.join('\n'));
const after = await eda.sys_FileManager.getDocumentSource();
const read = {};
for (const l of after.split('\n')) {
    const j = l.indexOf('||');
    if (j < 0) continue;
    let h, b;
    try { h = JSON.parse(l.slice(0, j)); b = JSON.parse(l.slice(j + 2).replace(/\|$/, '')); }
    catch (e) { continue; }
    if (h.type === 'ATTR' && (b.key in want) && b.parentId === '1') read[b.key] = b.y;
}
return {status: hits, writeReturned: ok, readBack: read, bodyBottom: -30};
