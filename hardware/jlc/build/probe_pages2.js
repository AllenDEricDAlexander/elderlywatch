const infos = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return (infos||[]).map(p => [p.uuid, p.name]);
