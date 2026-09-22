await eda.dmt_EditorControl.openDocument('e99e682aca69cae1');
const src = await eda.sys_FileManager.getDocumentSource();
const lines = src.split('\n');
let maxTicket=0, maxIe=0, maxLine=0, types={};
const keep=[];
for (const l of lines) {
  const i=l.indexOf('||'); if(i<0) continue;
  let h; try{h=JSON.parse(l.slice(0,i));}catch(e){continue;}
  maxTicket=Math.max(maxTicket,h.ticket||0);
  if (h.id && /^ie\d+$/.test(h.id)) maxIe=Math.max(maxIe, Number(h.id.slice(2)));
  if (h.id && /^line\d+$/.test(h.id)) maxLine=Math.max(maxLine, Number(h.id.slice(4)));
  types[h.type]=(types[h.type]||0)+1;
  if (h.type==='COMPONENT' && l.includes('"x":380,"y":305')) keep.push(l);
}
for (const l of lines) { const i=l.indexOf('||'); if(i<0) continue; const h=JSON.parse(l.slice(0,i)); const b=JSON.parse(l.slice(i+2).replace(/\|$/,'')); if (b.parentId && keep.some(k=>k.includes('"id":"'+h.id+'"')===false) && false) {} }
const parentIds = keep.map(k=>JSON.parse(k.slice(k.indexOf('||')+2).replace(/\|$/,'')).id);
for (const l of lines) { const i=l.indexOf('||'); if(i<0) continue; let h,b; try{h=JSON.parse(l.slice(0,i)); b=JSON.parse(l.slice(i+2).replace(/\|$/,''));}catch(e){continue;} if (parentIds.includes(b.parentId)) keep.push(l); }
const wl=[];
for (const l of lines) { if (l.includes('"startX":490,"startY":305')) wl.push(l); }
return {nlines:lines.length, maxTicket, maxIe, maxLine, types, keep, wl, tail: lines.slice(-3)};
