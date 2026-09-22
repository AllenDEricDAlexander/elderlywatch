await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const out = {};
for (const t of ['EasyEDA', 'Protel2', 'JLCEDA', undefined]) {
  try { const s = await eda.sch_Netlist.getNetlist(t); out[String(t)] = {len: (s||'').length, head: (s||'').slice(0, 200)}; }
  catch (e) { out[String(t)] = {error: String(e)}; }
}
return out;
