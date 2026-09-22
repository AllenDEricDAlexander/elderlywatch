return (await eda.dmt_Schematic.getAllSchematicPagesInfo())
    .map(p => ({uuid: p.uuid, name: p.title || p.name || p.friendlyName || ''}));
