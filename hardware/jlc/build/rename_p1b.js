const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return pages.filter(p => p.uuid === 'f0706db0ae88edcc').map(p => Object.fromEntries(Object.entries(p).filter(([k,v]) => typeof v !== 'object')));
