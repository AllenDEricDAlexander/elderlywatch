const t = __TYPE__;
const s = await eda.sch_Netlist.getNetlist(t);
return {length: (s||'').length, text: s};
