await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const src = await eda.sys_FileManager.getDocumentSource();
const recs=[];
for (const l of src.split('\n')) {
  const i=l.indexOf('||'); if(i<0) continue;
  let h,b; try{h=JSON.parse(l.slice(0,i)); b=JSON.parse(l.slice(i+2).replace(/\|$/,''));}catch(e){continue;}
  recs.push([h.type,h.id,b,l]);
}
const flag = recs.find(r=>r[0]==='COMPONENT' && r[2].x===380 && r[2].y===305);
const out={flagLine: flag[3]};
out.flagKids = recs.filter(r=>r[2].parentId===flag[1]).map(r=>r[3]);
const wire490 = recs.filter(r=>r[0]==='LINE' && r[2].startX===490 && r[2].startY===305);
out.wire = wire490.map(r=>r[3]);
out.wireGroup = wire490.length ? recs.filter(r=>r[0]==='WIRE' && r[1]===wire490[0][2].lineGroup).map(r=>r[3]) : [];
out.wireGroupKids = wire490.length ? recs.filter(r=>r[2].parentId===wire490[0][2].lineGroup).map(r=>r[3]) : [];
out.netAttrs = recs.filter(r=>r[0]==='ATTR' && r[2].key==='NET').length;
const u9 = recs.find(r=>r[0]==='COMPONENT' && r[2].x===600 && r[2].y===230);
out.u9kids = recs.filter(r=>r[2].parentId===u9[1]).map(r=>r[3]);
return out;
