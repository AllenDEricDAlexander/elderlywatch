const sym = '7ac0f6329abd612c', lib = 'ea905f22c789460e8404c7cb6b73ac04';
await eda.lib_Symbol.openInEditor(sym, lib);
const out = {};
try { out.docInfo = await eda.dmt_SelectControl.getCurrentDocumentInfo(); } catch (e) { out.docInfoErr = String(e); }
try { out.pinIds = await eda.sch_PrimitivePin.getAllPrimitiveId(); } catch (e) { out.pinErr = String(e); }
try { const all = await eda.sch_PrimitivePin.getAll(); out.count = all.length; out.first = all[0] ? {x: all[0].getState_X?.(), y: all[0].getState_Y?.(), num: all[0].getState_PinNumber?.(), name: all[0].getState_PinName?.(), rot: all[0].getState_Rotation?.()} : null; } catch (e) { out.getAllErr = String(e); }
try { out.rectIds = await eda.sch_PrimitiveRectangle.getAllPrimitiveId(); } catch (e) { out.rectErr = String(e); }
return out;
