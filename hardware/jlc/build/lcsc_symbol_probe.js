const ids = {U5:'C2682616', U6:'C54313', U7:'C109322', U9:'C962342'};
const out = {};
for (const [ref, lcsc] of Object.entries(ids)) {
  const it = (await eda.lib_Device.getByLcscIds([lcsc])).find(d => d.supplierId === lcsc);
  const symUuid = it.otherProperty?.Symbol, lib = it.libraryUuid;
  const sym = await eda.lib_Symbol.get(symUuid, lib);
  out[ref] = {lcsc, symUuid, type: typeof sym, keys: sym && typeof sym === 'object' ? Object.keys(sym) : null,
    snippet: sym && typeof sym === 'string' ? sym.slice(0, 400) : (sym ? JSON.stringify(sym).slice(0,400) : null)};
}
return out;
