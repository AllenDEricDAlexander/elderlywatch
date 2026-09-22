const t0 = Date.now();
await eda.dmt_EditorControl.openDocument('f0706db0ae88edcc');
const PROJ = 'ea905f22c789460e8404c7cb6b73ac04';
const out = {};
const t1 = Date.now();
let c = null, err = null;
try { c = await eda.sch_PrimitiveComponent.create({libraryUuid: PROJ, uuid: '86a999c80b83faa1'}, 900, -700, '1', 180, false, true, true); }
catch (e) { err = String(e && e.message || e).slice(0, 160); }
out.portCreateMs = Date.now() - t1;
out.err = err;
const g = (o, k) => { try { return o['getState_' + k](); } catch (e) { return 'ERR'; } };
if (c) {
    out.state = {id: c.getState_PrimitiveId(), type: g(c,'ComponentType'), net: g(c,'Net'), name: g(c,'Name'),
        desig: g(c,'Designator'), rot: g(c,'Rotation'), x: g(c,'X'), y: g(c,'Y')};
    c.done();
}
const t2 = Date.now();
const m = await eda.sch_PrimitiveComponent.modify('e07cf343cd3df50c', {designator: 'U7', name: 'TPS63070RNWR'});
out.modifyMs = Date.now() - t2;
out.afterModify = m ? {desig: g(m,'Designator'), name: g(m,'Name')} : null;
out.saved = await eda.sch_Document.save();
out.total = Date.now() - t0;
return out;
