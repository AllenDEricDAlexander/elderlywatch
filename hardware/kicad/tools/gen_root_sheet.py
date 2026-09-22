#!/usr/bin/env python3
"""Regenerate the root hierarchy sheet aiot-watch.kicad_sch.

UUIDs and sheet-instance paths of existing objects are preserved verbatim so
the netlist, ERC annotations and every child sheet's (instances (path ...))
keep resolving.
"""
import uuid

NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://example.invalid/aiot-watch/root-sheet")


def u(key: str) -> str:
    return str(uuid.uuid5(NS, key))


ROOT_UUID = "cfaf2e1b-398b-55f8-be91-353789ea1b53"
TOP_SHEET_UUID = "e9382dd4-19a4-54ec-8dcf-a4c010b13e39"
TOP_INSTANCE_PATH = f"/{ROOT_UUID}"

DATE = "2026-09-21"


def text(x, y, size, body, key, justify="left", bold=False):
    uuid_ = u(key)
    font = "(font (bold yes) (size {s} {s}))".format(s=size) if bold else "(font (size {s} {s}))".format(s=size)
    effects = f"(effects {font} (justify {justify}))"
    esc = body.replace("\\", "\\\\").replace('"', '\\"')
    return (f'(text "{esc}" (at {x} {y} 0) {effects} (uuid "{uuid_}"))')


blocks = []

# ---------------------------------------------------------------- sheet block
blocks.append(
    '(sheet (at 25.4 50.8) (size 139.7 76.2) (stroke (width 0.254) (type default)) '
    '(fill (color 0 0 0 0)) (uuid "' + TOP_SHEET_UUID + '") '
    '(property "Sheetname" "00_TOP" (at 25.4 48.26 0) '
    '(effects (font (bold yes) (size 2.5 2.5)) (justify left))) '
    '(property "Sheetfile" "schematic/00_TOP.kicad_sch" (at 25.4 129.54 0) '
    '(effects (font (size 1.27 1.27)) (justify left))) '
    '(instances (project "aiot-watch" (path "' + TOP_INSTANCE_PATH + '" (page "2")))))'
)

# text inside the root-level sheet box: index of the second level
INDEX = [
    ("page 3  01_POWER", "power"),
    ("page 4  02_ESP32", "mcu"),
    ("page 5  03_MODEM_SIM_RF", "cellular"),
    ("page 6  04_IMU_RTC", "motion/rtc"),
    ("page 7  05_DISPLAY", "hmi"),
    ("page 8  06_AUDIO", "audio"),
    ("page 9  07_HAPTIC_BUTTONS", "haptic/input"),
    ("page 10 08_DEBUG_TEST", "debug/fixture"),
]
y = 58.0
for label, tag in INDEX:
    blocks.append(text(29.21, y, 1.5, f"{label}   {tag}", "idx-" + tag))
    y += 8.0

blocks.append(text(25.4, 150.0, 1.4,
                   "Documented blockers and required inputs are tracked as D01-D16 in "
                   "docs/TODO_DATASHEET_VERIFY.md.", "docs-note"))

# ---------------------------------------------------------------- headings
blocks.append(text(25.4, 20, 3.5, "AIOT SENIOR WATCH - EVT-V1 ROOT SHEET", "title", bold=True))
blocks.append(text(25.4, 28, 1.6,
                   "EVT-V1 REVIEW DRAFT / NOT FOR FABRICATION / FOOTPRINTS & ERC PENDING",
                   "banner"))
blocks.append(text(25.4, 34, 1.4,
                   "This page carries no symbols and no wires on purpose: it is the document",
                   "cover-note-1a"))
blocks.append(text(25.4, 39, 1.4,
                   "cover and hierarchy index. All electrical content lives in 00_TOP and its",
                   "cover-note-1b"))
blocks.append(text(25.4, 44, 1.4,
                   "eight child sheets.", "cover-note-1c"))

# ---------------------------------------------------------------- right columns
X = 205.0
X2 = 310.0
blocks.append(text(X, 20, 2.2, "POWER TREE", "h-power", bold=True))
POWER = [
    "Pogo J1 5V (VBUS_5V)  -> U6 BQ24074 charger",
    "U6 OUT -> SYS         -> U7 TPS63070 buck-boost",
    "U7 VOUT -> +3V3_SYS   -> U1 ESP32-S3, sensors, logic",
    "U8 TLV75518 -> +1V8 (optional, not populated)",
    "VBAT -> U5 MAX17048 gauge; U6.TS battery NTC = OPEN",
    "VBAT -> modem feed    = NOT YET DESIGNED (D01/D09)",
]
y = 28.0
for i, line in enumerate(POWER):
    blocks.append(text(X, y, 1.4, line, f"pw-{i:02d}"))
    y += 7.0

blocks.append(text(X, y + 4, 2.2, "SHEET STATUS", "h-status", bold=True))
y += 11.0
STATUS = [
    "01  126 devices netlisted; U6/U7 reviewed",
    "    against TI datasheets",
    "02  ESP32-S3-PICO-1-N8R8 wired;",
    "    3 modem GPIO still unassigned",
    "03  SIM8230C / SIM / RF are pinless frames",
    "    - blocked on D01/D03",
    "04  BMI270 + RV-3028-C7 wired;",
    "    VBACKUP held per datasheet",
    "05  TFT frame pinless - blocked on D02",
    "06  ES8311 + PAM8302A drawn to real pin",
    "    tables; D15/D16 open",
    "07  DRV2605L + SOS/AI buttons wired",
    "08  21 test pads + pogo debug header",
]
for i, line in enumerate(STATUS):
    blocks.append(text(X, y, 1.4, line, f"st-{i:02d}"))
    y += 6.0

blocks.append(text(X2, 20, 2.2, "RELEASE GATE - HOLD", "h-gate", bold=True))
y = 28.0
GATE = [
    "Native ERC: 155 findings",
    "  (28 errors / 127 warnings) - exit 5",
    "Geometric DRC: 0 - only pads, test",
    "  points and outline exist on board",
    "Schematic parity: 105 devices have",
    "  no footprint binding",
    "Sourcing: 10 of 36 unique BOM lines",
    "  carry an MPN",
    "SPICE not run; no Gerber, placement",
    "  or RF review performed",
    "Sheets link by global labels, so this",
    "  root page has no hierarchical pins;",
    "  adding pins here would fake a",
    "  connectivity model the design lacks",
]
for i, line in enumerate(GATE):
    blocks.append(text(X2, y, 1.4, line, f"gt-{i:02d}"))
    y += 6.0

blocks.append(text(X2, y + 6, 2.2, "EVIDENCE", "h-ev", bold=True))
y += 13.0
EV = [
    "docs/NATIVE_CHECK.json",
    "docs/ERC_DRC_REPORT.md",
    "docs/KICAD_HAPPY_REVIEW.md",
    "docs/KICAD_HAPPY_RUN.json",
    "docs/TODO_DATASHEET_VERIFY.md  D01-D16",
]
for i, line in enumerate(EV):
    blocks.append(text(X2, y, 1.4, line, f"ev-{i:02d}"))
    y += 6.0

blocks.append(text(X2, y + 6, 2.2, "HOW TO REPRODUCE", "h-repro", bold=True))
y += 13.0
REPRO = [
    "python3 hardware/kicad/tools/validate_draft.py",
    "python3 hardware/kicad/tools/check_kicad.py",
    "kicad-cli 10.0.6; ERC/DRC keep",
    "  --exit-code-violations",
]
for i, line in enumerate(REPRO):
    blocks.append(text(X2, y, 1.4, line, f"rp-{i:02d}"))
    y += 6.0

body = "\n".join(blocks)

out = (
    '(kicad_sch (version 20231120) (generator "aiot_watch_review") '
    f'(uuid "{ROOT_UUID}") (paper "A3") '
    # KiCad 10's schematic parser rejects (comment ...) inside title_block;
    # comment text is carried as ordinary text objects on the page instead.
    '(title_block (title "AIOT SENIOR WATCH - EVT-V1 SYSTEM HIERARCHY") '
    f'(date "{DATE}") (rev "EVT-V1 REVIEW ONLY") (company "elderlywatch")) '
    "(lib_symbols)\n"
    f"{body}\n"
    f'(sheet_instances (path "/" (page "1"))))\n'
)

print(out, end="")
