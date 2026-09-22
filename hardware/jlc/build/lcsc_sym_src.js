const tab = await eda.dmt_EditorControl.openDocument('45084536032c46b0b6a1fbb04d5d2f07');
const src = await eda.sys_FileManager.getDocumentSource();
return {tab, len: src ? src.length : 0, head: src ? src.slice(0, 200) : null};
