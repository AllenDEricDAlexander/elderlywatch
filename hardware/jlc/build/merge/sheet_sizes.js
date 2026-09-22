const names = ['Drawing-Symbol_A0', 'Drawing-Symbol_A1', 'Drawing-Symbol_E', 'Drawing-Symbol_D', 'Drawing-Symbol_C', 'Drawing-Symbol_A4'];
const out = [];
for (const n of names) {
    const hits = await eda.lib_Device.search(n, undefined, undefined, undefined, 5, 1);
    const d = (hits || []).find(x => x.name === n);
    if (!d) { out.push({name: n, found: false}); continue; }
    const op = d.otherProperty || {};
    out.push({name: n, uuid: d.uuid, lib: d.libraryUuid,
        width: op.Width || op.width || null, height: op.Height || op.height || null,
        size: op['Page Size'] || op.Size || null, keys: Object.keys(d).join(',')});
}
return out;
