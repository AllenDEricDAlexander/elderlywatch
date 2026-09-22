const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const r = await eda.sch_PrimitiveRectangle.get('ie0');
const methods = [];
let o = r;
while (o && o !== Object.prototype) { methods.push(...Object.getOwnPropertyNames(o)); o = Object.getPrototypeOf(o); }
const g = {};
for (const k of [...new Set(methods)]) { if (!/^get/.test(k)) continue; try { const v = r[k](); if (v === null || typeof v !== 'object') g[k] = v; } catch (e) {} }
return {methods: [...new Set(methods)].filter(k => /^get|^set|^done/.test(k)), state: g};
