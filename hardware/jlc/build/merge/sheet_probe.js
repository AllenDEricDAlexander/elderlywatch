const hits = await eda.lib_Device.search('Drawing-Symbol', undefined, undefined, undefined, 40, 1);
const out = (hits || []).map(d => ({name: d.name, uuid: d.uuid, lib: d.libraryUuid,
    size: (d.otherProperty && (d.otherProperty['Page Size'] || d.otherProperty.Width)) || null}));
const syms = await eda.lib_Symbol.search('Drawing-Symbol', undefined, undefined, undefined, 40, 1);
return {devices: out.slice(0, 20), symbols: (syms || []).map(s => ({name: s.name, uuid: s.uuid, lib: s.libraryUuid})).slice(0, 20)};
