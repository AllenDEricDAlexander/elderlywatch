const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const all = await eda.sch_PrimitivePin.getAll();
const one = all[0];
const methods = [];
let o = one;
while (o && o !== Object.prototype) { methods.push(...Object.getOwnPropertyNames(o).filter(k => typeof one[k] === 'function')); o = Object.getPrototypeOf(o); }
const snap = (p) => { const g = {}; for (const k of [...new Set(methods)]) { if (!/^get(State|_)/.test(k)) continue; try { const v = p[k](); if (typeof v !== 'object') g[k] = v; } catch (e) {} } return g; };
const nums = all.map(p => p.getState_PinNumber ? p.getState_PinNumber() : null);
const pick = (n) => all[nums.indexOf(n)];
return {methods: [...new Set(methods)].filter(k => /^get|^set/.test(k)), p1: snap(pick('1')), p10: snap(pick('10')), p11: snap(pick('11'))};
