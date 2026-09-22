await eda.dmt_EditorControl.openDocument('52caa9452ee66dee');
let names = null, err = null;
try { names = await eda.pcb_Net.getAllNetName(); } catch (e) { err = String(e); }
let comps = null;
try { comps = (await eda.pcb_PrimitiveComponent.getAll()).length; } catch (e) { comps = String(e); }
return {netCount: names ? names.length : null, nets: names, err: err, pcbComponents: comps};
