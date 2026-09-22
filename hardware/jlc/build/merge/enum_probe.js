const e = eda;
const grab = name => { const m = e[name]; return m ? Object.fromEntries(Object.entries(m).filter(([k,v]) => typeof v === 'number').slice(0, 20)) : null; };
return {
  align: grab('ESCH_PrimitiveTextAlignMode'),
  lineType: grab('ESCH_PrimitiveLineType'),
  layer: Object.keys(e).filter(k => /^ESCH_/.test(k)).join(','),
};
