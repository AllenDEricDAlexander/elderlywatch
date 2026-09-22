const PROJ = 'ea905f22c789460e8404c7cb6b73ac04';
const r = {steps: []};
try {
  const o = await eda.lib_Symbol.openInEditor('8053ebf70429046d', PROJ);
  r.steps.push(['openInEditor', typeof o === 'object' ? JSON.stringify(o).slice(0,120) : String(o)]);
} catch (e) { r.steps.push(['openInEditor threw', e.message]); }
try {
  const s = await eda.sys_FileManager.getDocumentSource();
  r.srcLen = s ? s.length : 0;
  r.head = s ? s.slice(0, 160) : null;
  r.pinAttrLines = s ? s.split('\n').filter(l => l.indexOf('Pin Number') >= 0).slice(0, 12) : [];
} catch (e) { r.readErr = e.message; }
r.current = await eda.dmt_SelectControl.getCurrentDocumentInfo();
return r;
