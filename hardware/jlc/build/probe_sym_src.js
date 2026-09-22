const sym='7ac0f6329abd612c', lib='ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const lines = src.split('\n');
let maxTicket=0, ids=new Set(), types={};
for (const l of lines) {
  const i=l.indexOf('||'); if(i<0) continue;
  let h; try{h=JSON.parse(l.slice(0,i));}catch(e){continue;}
  if (h.ticket>maxTicket) maxTicket=h.ticket;
  if (h.id) ids.add(h.id);
  types[h.type]=(types[h.type]||0)+1;
}
return {nlines: lines.length, maxTicket, idCount: ids.size, types, rect: lines.filter(l=>l.includes('"RECT"')), tail: lines.slice(-4), pinSample: lines.filter(l=>l.includes('"type":"PIN"')).slice(0,1)};
