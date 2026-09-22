const t0 = Date.now();
await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const out = {marks: {}};
let c = null;
const t1 = Date.now();
try { c = await eda.sch_PrimitiveComponent.createNetPort('BI', 'LCD_SCLK', 900, -500, 180, false); }
catch (e) { out.err = String(e && e.message || e).slice(0, 200); }
out.marks.netPortMs = Date.now() - t1;
out.id = c ? c.getState_PrimitiveId() : null;
if (c) {
    const g = k => { try { return c['getState_' + k](); } catch (e) { return 'ERR'; } };
    out.state = {type: g('ComponentType'), net: g('Net'), name: g('Name'), desig: g('Designator'),
        rot: g('Rotation'), x: g('X'), y: g('Y'), component: g('Component'), symbol: g('Symbol')};
    c.done();
}
out.saved = await eda.sch_Document.save();
out.total = Date.now() - t0;
return out;
