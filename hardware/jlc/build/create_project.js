// Create (or reuse) the EasyEDA Pro project and the 8 functional pages that
// mirror hardware/kicad/schematic/. Idempotent: existing names are matched, never
// duplicated, and it refuses to run while another project has unsaved work.

const PROJECT_NAME = "aiot-watch-jlc";
const PROJECT_DESCRIPTION = "AIOT SENIOR WATCH EVT-V1 - JLC adaptation of hardware/kicad. REVIEW DRAFT, NOT FOR FABRICATION.";

// Page names come from ../kicad/schematic/*.kicad_sch. 00_TOP is the hierarchy
// cover in KiCad; on the JLC side the top page carries the power tree instead,
// because EasyEDA Pro has no hierarchical sheet objects to index.
const PAGES = [
  "00_TOP",
  "01_POWER",
  "02_ESP32",
  "03_MODEM_SIM_RF",
  "04_IMU_RTC",
  "05_DISPLAY",
  "06_AUDIO",
  "07_HAPTIC_BUTTONS",
  "08_DEBUG_TEST",
];

const openedNow = await eda.dmt_Project.getCurrentProjectInfo();
if (openedNow) {
  throw new Error(
    "A project is already open (" + (openedNow.friendlyName || openedNow.name) +
    "). Close it in EasyEDA first - openProject discards unsaved work."
  );
}

let projectUuid = null;
const projectNames = [];
for (const uuid of (await eda.dmt_Project.getAllProjectsUuid()) || []) {
  const info = await eda.dmt_Project.getProjectInfo(uuid);
  const name = info && (info.friendlyName || info.name);
  projectNames.push(name);
  if (name === PROJECT_NAME) {
    projectUuid = uuid;
  }
}

const created = { projectReused: Boolean(projectUuid) };
if (!projectUuid) {
  projectUuid = await eda.dmt_Project.createProject(
    PROJECT_NAME, PROJECT_NAME, undefined, undefined, PROJECT_DESCRIPTION);
  if (!projectUuid) {
    throw new Error("createProject returned undefined; seen projects: " + projectNames.join(", "));
  }
}

if (!(await eda.dmt_Project.openProject(projectUuid))) {
  throw new Error("openProject failed for " + projectUuid);
}

let schematics = await eda.dmt_Schematic.getAllSchematicsInfo();
let schematic = (schematics || [])[0];
if (!schematic) {
  const schematicUuid = await eda.dmt_Schematic.createSchematic();
  if (!schematicUuid) {
    throw new Error("createSchematic failed");
  }
  created.schematicUuid = schematicUuid;
  schematics = await eda.dmt_Schematic.getAllSchematicsInfo();
  schematic = (schematics || [])[0];
}

const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
const byName = {};
for (const page of pages || []) {
  if (page.parentSchematicUuid === schematic.uuid) {
    byName[page.name] = page;
  }
}

const pageMap = [];
const createdPages = [];
for (const name of PAGES) {
  let page = byName[name];
  if (!page) {
    const pageUuid = await eda.dmt_Schematic.createSchematicPage(schematic.uuid);
    if (!pageUuid) {
      throw new Error("createSchematicPage failed for " + name);
    }
    createdPages.push(name);
    page = (await eda.dmt_Schematic.getAllSchematicPagesInfo())
      .find((p) => p.uuid === pageUuid);
    if (page && page.name !== name) {
      await eda.dmt_Schematic.modifySchematicPageName(page.uuid, name);
      page.name = name;
    }
  }
  pageMap.push({ name, uuid: page ? page.uuid : null });
}

const firstTabId = await eda.dmt_EditorControl.openDocument(pageMap[0].uuid);

return {
  projectUuid,
  schematicUuid: schematic.uuid,
  schematicName: schematic.name,
  pageMap,
  firstTabId,
  created,
  createdPages,
};
