#!/usr/bin/env python3
"""Rebuild all nine functional schematic pages on one sheet, so the whole design fits one view.

The KiCad import put one sheet per functional block into 嘉立创EDA (00_TOP … 08_DEBUG_TEST).
That mirrors KiCad's hierarchy but nobody can read the board as a whole from it, so this
tool copies every primitive of those pages onto a single generated page named `10_ALL`,
arranged as the 3x3 functional map in `MAP` - power feeding the controller on the left, the
controller in the middle with its peripherals around it, the modem/RF chain on its own row.
Net names are the same across the blocks, so on one sheet the same-nets join up by
themselves - which is exactly what makes it a *complete* schematic rather than a collage.

Why the copy goes primitive-by-primitive instead of by pasting document source: `
sys_FileManager.setDocumentSource()` and `lib_Symbol.updateDocumentSource()` are edit-only -
they accept in-place field changes but return `false` for any appended record (re-tested on a
scratch page on 2026-09-21: `writeReturned: false`, record count unchanged). So the merge has
to re-create through `sch_PrimitiveComponent/Wire/Text/Polygon.create()`.

What fidelity means here:
  * positions come from `getState_*()` in API units and each page is shifted by one constant
    offset, so a wire that ended exactly on a pin tip still ends on that pin tip after the
    shift - connectivity is data (wire NET attribute + netport net), and the geometry that
    the parity gate resolves through is preserved;
  * the page frame (`componentType === 'sheet'`) is skipped - the nine inherited A4 frames
    frame a fraction of what they were given, so the merged sheet draws its own border, its
    partition frames and its title block from rectangles and text instead (`decorations()`);
  * designators, names, nets, rotation, mirror, sub-part and BOM/PCB flags are re-applied per
    component so `U3`, `C101` … stay addressable and unique.

This page is GENERATED OUTPUT and a READING VIEW: re-running wipes it (circuitry, border and
partitions alike) and rebuilds it; `--incremental` keeps what is already correct and only places
what the sheet is missing. Never hand-edit `10_ALL` - edit the source pages and re-merge. It is
also a copy, so the nine original pages remain the place where design changes belong *and* the
only place the PCB netlist and the BOM are read from: every part placed here is created with
`addIntoBom=false / addIntoPcb=false`, so the duplicated designators stay out of any transfer.

Never trust create(). Measured on 2026-09-21: `sch_PrimitiveWire.create()` answers "create
failed!" for wires that did land, and a batch the editor chokes on dies with the bridge's 30s
timeout *after* its primitives were written. So the merge is a verify loop, not a retry loop:
each round reads the live sheet back (`VERIFY`), matches every expected primitive to a live one
by geometry within a tolerance, creates only what is genuinely absent, repairs attributes
(designator, name, net) with modify(), and reports duplicates. Only that diff decides
PASS/FAIL - a batch's own failure list is logged as information, never acted on, because
re-creating something that is already on the sheet would put a second `U3` on the page and
break both the netlist and the BOM.

    python3 hardware/jlc/tools/merge_schematic_pages.py                     # all nine, from scratch
    python3 hardware/jlc/tools/merge_schematic_pages.py --incremental       # resume after a hang
    python3 hardware/jlc/tools/merge_schematic_pages.py --pages 05_DISPLAY  # one tile only
    python3 hardware/jlc/tools/merge_schematic_pages.py --read-only         # dump only

Exit code 0 means every expected primitive is on the sheet with the right attributes and
nothing is left over; verify it independently with tools/check_sch_netlist_parity.py --page
10_ALL.
"""
import argparse
import csv
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402

BUILD = HERE.parent / "build"
MERGE = BUILD / "merge"
LAYOUT = MERGE / "layout.json"

TARGET_NAME = "10_ALL"
SOURCE = re.compile(r"^0\d_")           # 00_TOP … 08_DEBUG_TEST - deliberately NOT `10_ALL`,
                                       # which must never be an input to itself
# The nine imported pages carry an A4 `sheet` symbol each - the importer's doing, not a
# decision, and it is what made blocks look like they "spilled outside the drawing": the
# content of a page is up to 1.9x taller and wider than the A4 border (1170 x 825) it was
# given. No library frame fits the merged map either (largest available is A0,
# 4676 x 3304, against a content map of 6930 x 5254), so `10_ALL` drops the symbol and
# draws its own border instead - see `decorations()`. Flipping this to True keeps the
# inherited A4 frame, with the same overflow.
KEEP_FRAME = False
# Never copied from a source page: `sheet` is each page's own title frame and
# `block_symbol` is 00_TOP's hierarchical child-sheet blocks - the merged sheet holds those
# sheets flat, so re-drawing the blocks would point the design at itself. 00_TOP still
# contributes its review notes, which are plain TEXT primitives (RELEASE GATE banner included).
SKIP = ["sheet", "block_symbol"]
GAP = 400                                # API units between blocks; >> the 0.01 parity tolerance

# ---- sheet furniture (all in API units; 1 unit = 10mil, and +y points UP) -------------
# The numbers below are what the 2026-09-21 probes settled: `sch_PrimitiveText.create()`'s
# alignMode parameter is ESCH_PrimitiveTextAlignMode verbatim (1=LEFT_TOP … 9=RIGHT_BOTTOM;
# 0 silently becomes 3), a TOP anchor hangs the glyphs *down* by the font size, colors
# round-trip as '#RRGGBB', and 0/null means the theme's own ink.
INK = "#808080"          # border / title block - grey reads on both the light and dark theme
PART_INK = "#FF9900"     # partition frames - amber, so they never look like circuitry
BORDER_W = 25
INNER_W = 10
FRAME_W = 8
BLOCK_W = 12
MARGIN = 250             # outer border -> nearest partition frame
INNER_INSET = 110        # second border line, drawn inside the first
FRAME_PAD = 40           # partition frame -> block content, left and right
# The partition frame may not crowd out its neighbour. Rows are separated by GAP plus the
# height difference of the two rows they divide, so the tightest pair on the map is
# 01_POWER -> 03_MODEM at 305.7 units, not 400: head band + foot band has to stay under that
# (85 + 164 = 249, leaving ~57 units of air between those two amber lines). Every other
# facing pair is 533 or more.
TITLE_TOP_GAP = 20       # frame line -> partition title
TITLE_FS = 45            # partition title height
TITLE_BAND = TITLE_TOP_GAP * 2 + TITLE_FS
NOTE_X = 60              # remark inset from the partition frame's left edge
NOTE_TOP_GAP = 25        # content -> first remark line
NOTE_FS = 30
NOTE_LINE = 42           # baseline-to-baseline for remark lines
NOTE_BOTTOM_GAP = 25
NOTES_MAX = 3            # see the head/foot budget above - BLOCK_META honours it
TB_W = 2550              # title block width
TB_H = 560               # title block height
TB_SIDE = 145            # title block's offset from the inner border line
BANNER_FS = 55
# The review-draft date of the map, not the date this tool last ran: a build timestamp in
# the title block would make every re-run rewrite the page for nothing.
SHEET_DATE = "2026-09-21"

# Functional map: (row, column) per block, read as signal flow - row 0 is the top of the
# sheet, column 0 the left. The controller sits in the middle with what feeds it (power)
# and what it drives (display, IMU/RTC) around it; the modem/RF chain gets its own row
# because it is both the widest and the least MCU-adjacent block; 00_TOP's review notes
# land bottom-right, where they stay visible without covering circuitry.
MAP = {
    "01_POWER": (0, 0), "02_ESP32": (0, 1), "05_DISPLAY": (0, 2),
    "03_MODEM_SIM_RF": (1, 0), "06_AUDIO": (1, 1), "04_IMU_RTC": (1, 2),
    "07_HAPTIC_BUTTONS": (2, 0), "08_DEBUG_TEST": (2, 1), "00_TOP": (2, 2),
}

# Per-partition header and remarks. The wording is the English note text that 00_TOP already
# carries, translated - nothing here is a claim the source pages do not make. Each block gets
# one amber frame, one title above its content and its remarks below, so the map reads as nine
# functions instead of a cloud of wires.
BLOCK_META = {
    "01_POWER": ("电源与充电  01_POWER", [
        "VBUS_5V → BQ24074(U6) → SYS 供电路径管理",
        "SYS → TPS63070(U7) → +3V3_SYS 升降压；MAX17048(U5) 电量计 + NTC",
        "VBAT 直供 4G 模组：该路径待复核；+1V8 为可选轨"]),
    "02_ESP32": ("主控  02_ESP32", [
        "U1 = ESP32-S3-PICO-1-N8R8：Wi-Fi + BLE",
        "对外总线：I2C / SPI / I2S0 / PCM / UART；USB + BOOT + RESET 烧录夹具",
        "GPIO 控制余量紧张：尚有 3 个网络未定"]),
    "03_MODEM_SIM_RF": ("4G 模组 / SIM / RF  03_MODEM_SIM_RF", [
        "U2 = SIM8230C 未选型 → 符号无引脚，网表不含其连接",
        "Nano SIM 卡座 + eSIM 选项；MAIN / DIV / GNSS 三路天线 + Wi-Fi RF",
        "UART / PCM 电平转换待定；HDG 引脚映射与焊盘被阻塞"]),
    "04_IMU_RTC": ("姿态与环境  04_IMU_RTC", [
        "BMI270(U3)：IMU_INT1 / IMU_INT2；RV-3028-C7(U4)：RTC_INT",
        "共用 I2C_SCL / I2C_SDA / 3V3",
        "布板要求：置于表体中心、完整地"]),
    "05_DISPLAY": ("显示  05_DISPLAY", [
        "SPI TFT 240×280 / 1.69 英寸：LCD_SCLK / MOSI / CS / DC",
        "LCD_RST / LCD_BL 控制",
        "FPC 连接器、LED 驱动与触摸均未定"]),
    "06_AUDIO": ("音频  06_AUDIO", [
        "ES8311(U9) + 模拟 MEMS 麦 + PAM8302A(U10)；喇叭为差分 BTL 输出",
        "I2S0 / MCLK / I2C 控制",
        "编解码手册目前是第三方镜像版（仅限内部评审）；声学待定"]),
    "07_HAPTIC_BUTTONS": ("触觉与按键  07_HAPTIC_BUTTONS", [
        "DRV2605L(U11) → LRA 或 ERM 马达",
        "BTN_SOS → GPIO1、BTN_AI → GPIO2（直连）",
        "按键各自 1k / 100n 滤波"]),
    "08_DEBUG_TEST": ("调试与测试  08_DEBUG_TEST", [
        "4-pin pogo 触点：5V / GND / TX / RX；ESP USB 与 MODEM USB 引出",
        "底部 21 个命名测试盘",
        "ESD 与夹具结构待定"]),
    "00_TOP": ("设计索引与发布说明  00_TOP", [
        "本页为 00–08 九页合并出的阅读视图",
        "网表与 BOM 只从九个源页取，本页器件全部排除",
        "发布闸门 HOLD：未布板、不产出 Gerber；缺手册的器件仍阻塞评审"]),
}

PAGES = """
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return pages.map(p => ({uuid: p.uuid, name: p.title || p.name || p.friendlyName || ''}));
"""

ENSURE_TARGET = """
const name = __NAME__;
let pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
let hit = pages.find(p => (p.title || p.name || '') === name);
if (hit) return {uuid: hit.uuid, name: name, created: false, pages: pages.length};
const schematic = ((pages.find(p => (p.title || p.name || '') === 'aiot-watch')
    || pages.find(p => p.parentSchematicUuid) || {}).parentSchematicUuid);
if (!schematic) throw new Error('no schematic uuid on any page - cannot add a sheet');
const uuid = await eda.dmt_Schematic.createSchematicPage(schematic);
if (!uuid) throw new Error('createSchematicPage() returned nothing');
await eda.dmt_Schematic.modifySchematicPageName(uuid, name);
pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return {uuid: uuid, name: name, created: true, renamed: (pages.find(p => p.uuid === uuid) || {}).name,
    pages: pages.length};
"""

READ = """
const page = __PAGE__;
await eda.dmt_EditorControl.openDocument(page);
function state(o, keys) {
    const rec = {};
    for (const k of keys) {
        try { const v = o['getState_' + k](); rec[k] = (v === undefined ? null : v); } catch (e) { rec[k] = null; }
    }
    return rec;
}
const comps = await eda.sch_PrimitiveComponent.getAll();
const components = comps.map(c => state(c, ['PrimitiveId', 'ComponentType', 'Designator',
    'Name', 'Net', 'X', 'Y', 'Rotation', 'Mirror', 'SubPartName', 'AddIntoBom', 'AddIntoPcb',
    'Component']));
const wires = (await eda.sch_PrimitiveWire.getAll()).map(w => state(w,
    ['PrimitiveId', 'Line', 'Net', 'Color', 'LineWidth', 'LineType']));
const texts = (await eda.sch_PrimitiveText.getAll()).map(t => state(t, ['PrimitiveId', 'X', 'Y',
    'Content', 'Rotation', 'TextColor', 'FontName', 'FontSize', 'Bold', 'Italic', 'UnderLine',
    'AlignMode']));
const polys = (await eda.sch_PrimitivePolygon.getAll()).map(p => state(p,
    ['PrimitiveId', 'Line', 'Color', 'FillColor', 'LineWidth', 'LineType']));
const content = components.filter(c => __SKIP__.indexOf(c.ComponentType) < 0);
const ids = [].concat(content.map(c => c.PrimitiveId), wires.map(w => w.PrimitiveId),
    texts.map(t => t.PrimitiveId), polys.map(p => p.PrimitiveId));
const bbox = ids.length ? await eda.sch_Primitive.getPrimitivesBBox(ids) : null;
return {counts: {components: components.length, wires: wires.length, texts: texts.length,
    polys: polys.length}, bbox: bbox, components: components, wires: wires, texts: texts,
    polys: polys};
"""

RESET = """
const target = __TARGET__;
await eda.dmt_EditorControl.openDocument(target);
// Everything goes, the imported `sheet` frame included - `decorations()` draws the
// replacement border. Keeping __KEEP__ alive instead would leave an A4 box around an
// A2-sized block of circuitry, which is the very defect this pass exists to remove.
const mods = [['component', eda.sch_PrimitiveComponent, __KEEP__], ['wire', eda.sch_PrimitiveWire, null],
    ['text', eda.sch_PrimitiveText, null], ['poly', eda.sch_PrimitivePolygon, null],
    ['rect', eda.sch_PrimitiveRectangle, null]];
const gone = {};
for (const [kind, mod, keep] of mods) {
    const ids = [];
    for (const p of await mod.getAll()) {
        let type = null;
        try { type = p.getState_ComponentType(); } catch (e) {}
        if (keep && type === keep) continue;
        ids.push(p.getState_PrimitiveId());
    }
    let removed = 0;
    if (ids.length) { removed = (await mod.delete(ids)) ? ids.length : 0; }
    gone[kind] = {found: ids.length, removed: removed};
}
const saved = await eda.sch_Document.save();
return {gone: gone, saved: saved};
"""

OPEN = """
const target = __TARGET__;
const tab = await eda.dmt_EditorControl.openDocument(target);
return {tab: tab};
"""

VERIFY = """
const r = v => (v === undefined || v === null ? null : Math.round(v * 1000) / 1000);
const parts = [], ports = [], flags = [], frames = [], wires = [], texts = [], polys = [], rects = [];
for (const c of await eda.sch_PrimitiveComponent.getAll()) {
    const type = c.getState_ComponentType();
    let net = null;
    try { net = c.getState_Net(); } catch (e) {}
    let name = null;
    try { name = c.getState_Name(); } catch (e) {}
    const rec = {id: c.getState_PrimitiveId(), x: r(c.getState_X()), y: r(c.getState_Y()),
        designator: c.getState_Designator(), name: name, net: net === undefined ? name : (net || name),
        bom: c.getState_AddIntoBom(), pcb: c.getState_AddIntoPcb()};
    // A page frame is reported as its own bucket, never as a `part`: it has no designator,
    // and it must never be mistaken for one in diff() - the merged sheet's frame is drawn
    // from rectangles instead, so any `sheet` symbol on it is a leftover to delete.
    if (type === 'sheet') frames.push(rec);
    else if (type === 'netport') ports.push(rec);
    else if (type === 'netflag') flags.push(rec);
    else parts.push(rec);
}
for (const w of await eda.sch_PrimitiveWire.getAll())
    wires.push({id: w.getState_PrimitiveId(), line: w.getState_Line().map(r), net: w.getState_Net()});
for (const t of await eda.sch_PrimitiveText.getAll())
    texts.push({id: t.getState_PrimitiveId(), x: r(t.getState_X()), y: r(t.getState_Y()),
        content: t.getState_Content()});
for (const p of await eda.sch_PrimitivePolygon.getAll())
    polys.push({id: p.getState_PrimitiveId(), line: p.getState_Line().map(r)});
for (const q of await eda.sch_PrimitiveRectangle.getAll())
    rects.push({id: q.getState_PrimitiveId(),
        box: [r(q.getState_TopLeftX()), r(q.getState_TopLeftY()), r(q.getState_Width()),
            r(q.getState_Height())]});
return {parts: parts, ports: ports, flags: flags, frames: frames, wires: wires, texts: texts,
    polys: polys, rects: rects};
"""

# NOTE: no openDocument() in here. It runs once per batch, the target sheet is already the
# active document, and re-opening a sheet that holds a thousand primitives is what cost a
# 30s bridge timeout mid-run on 2026-09-21.
CREATE = """
const project = __PROJECT__, items = __ITEMS__, stop = __STOP__;
const made = {}, failed = [];
const bump = kind => { made[kind] = (made[kind] || 0) + 1; };
let streak = 0;
for (const it of items) {
    if (streak >= stop) {
        failed.push([it.i, it.k, it.label, 'abandoned - the client kept refusing creates']);
        continue;
    }
    try {
        if (it.k === 'part') {
            const c = await eda.sch_PrimitiveComponent.create({libraryUuid: project, uuid: it.uuid},
                it.x, it.y, it.subPartName, it.rotation, it.mirror, it.addIntoBom, it.addIntoPcb);
            if (!c) { failed.push([it.i, it.k, it.label, 'create() returned nothing']); streak++; continue; }
            if (c.done) c.done();
            if (it.designator || it.name) {
                const prop = {};
                if (it.designator) prop.designator = it.designator;
                if (it.name) prop.name = it.name;
                const m = await eda.sch_PrimitiveComponent.modify(c.getState_PrimitiveId(), prop);
                if (!m) { failed.push([it.i, it.k, it.label, 'modify() returned nothing']); streak++; continue; }
            }
            bump('part');
        } else if (it.k === 'port') {
            const c = await eda.sch_PrimitiveComponent.createNetPort(it.direction, it.net, it.x,
                it.y, it.rotation, it.mirror);
            if (!c) { failed.push([it.i, it.k, it.label, 'createNetPort() returned nothing']); streak++; continue; }
            if (c.done) c.done();
            bump('port');
        } else if (it.k === 'flag') {
            const c = await eda.sch_PrimitiveComponent.createNetFlag(it.identification, it.net,
                it.x, it.y, it.rotation, it.mirror);
            if (!c) { failed.push([it.i, it.k, it.label, 'createNetFlag() returned nothing']); streak++; continue; }
            if (c.done) c.done();
            bump('flag');
        } else if (it.k === 'wire') {
            const w = await eda.sch_PrimitiveWire.create(it.line, it.net, it.color, it.lineWidth,
                it.lineType);
            if (!w) {
                failed.push([it.i, it.k, it.label, 'create() returned nothing']);
                await eda.sch_Document.save();
                streak++;
                continue;
            }
            if (w.done) w.done();
            await eda.sch_Document.save();
            bump('wire');
        } else if (it.k === 'text') {
            const t = await eda.sch_PrimitiveText.create(it.x, it.y, it.content, it.rotation,
                it.textColor, it.fontName, it.fontSize, it.bold, it.italic, it.underLine,
                it.alignMode);
            if (!t) { failed.push([it.i, it.k, it.label, 'create() returned nothing']); streak++; continue; }
            if (t.done) t.done();
            bump('text');
        } else if (it.k === 'poly') {
            const pp = await eda.sch_PrimitivePolygon.create(it.line, it.color, it.fillColor,
                it.lineWidth, it.lineType);
            if (!pp) { failed.push([it.i, it.k, it.label, 'create() returned nothing']); streak++; continue; }
            if (pp.done) pp.done();
            bump('poly');
        } else if (it.k === 'rect') {
            // topLeftY is the *upper* edge: rectangles grow downwards from the anchor, which
            // is the same handedness the text TOP anchors show (+y is up on this canvas).
            const q = await eda.sch_PrimitiveRectangle.create(it.box[0], it.box[1], it.box[2],
                it.box[3], 0, 0, it.color, null, it.lineWidth, 0, null);
            if (!q) { failed.push([it.i, it.k, it.label, 'create() returned nothing']); streak++; continue; }
            if (q.done) q.done();
            bump('rect');
        } else if (it.k === 'fix_part') {
            const m = await eda.sch_PrimitiveComponent.modify(it.id, it.prop);
            if (!m) { failed.push([it.i, it.k, it.label, 'modify() returned nothing']); streak++; continue; }
            bump('fix_part');
        } else if (it.k === 'fix_wire') {
            const m = await eda.sch_PrimitiveWire.modify(it.id, {net: it.net});
            if (!m) { failed.push([it.i, it.k, it.label, 'modify() returned nothing']); streak++; continue; }
            bump('fix_wire');
        } else if (it.k.startsWith('drop_')) {
            const mod = it.k === 'drop_wire' ? eda.sch_PrimitiveWire : it.k === 'drop_text'
                ? eda.sch_PrimitiveText : it.k === 'drop_poly' ? eda.sch_PrimitivePolygon
                : it.k === 'drop_rect' ? eda.sch_PrimitiveRectangle
                : eda.sch_PrimitiveComponent;
            const m = await mod.delete([it.id]);
            if (!m) { failed.push([it.i, it.k, it.label, 'delete() returned nothing']); streak++; continue; }
            bump('drop');
        } else {
            failed.push([it.i, it.k, it.label, 'unknown kind']);
            streak++;
            continue;
        }
    } catch (e) {
        failed.push([it.i, it.k, it.label, String(e && e.message || e).slice(0, 120)]);
        streak++;
        continue;
    }
    streak = 0;
}
const saved = await eda.sch_Document.save();
return {made: made, failed: failed, saved: saved};
"""


def page_records():
    return [p for p in execute(PAGES) if p["uuid"]]


def read_pages(names):
    """Dump each source page's primitive states to build/merge/<page>.json."""
    MERGE.mkdir(parents=True, exist_ok=True)
    dumps = {}
    for name in names:
        path = MERGE / f"{name}.json"
        dump = json.loads(path.read_text()) if path.exists() else None
        if dump is None:
            uuid = {p["name"]: p["uuid"] for p in page_records()}[name]
            dump = execute(READ.replace("__PAGE__", json.dumps(uuid))
                           .replace("__SKIP__", json.dumps(SKIP)))
            path.write_text(json.dumps(dump, ensure_ascii=False))
        dumps[name] = dump
        box = dump["bbox"] or {}
        print(f"read {name:<18} comps={dump['counts']['components']:>4} "
              f"wires={dump['counts']['wires']:>4} texts={dump['counts']['texts']:>3} "
              f"polys={dump['counts']['polys']:>3} "
              f"bbox={box.get('minX')},{box.get('minY')}..{box.get('maxX')},{box.get('maxY')}",
              file=sys.stderr)
    return dumps


def layout(dumps, gap=GAP):
    """Put each block in its cell of the functional map (see MAP), aligned top-left.

    Blocks are placed in API units (y grows upwards) and each one keeps its internal
    geometry untouched - only one constant offset per block - so a wire that ended on a
    pin tip still ends on that pin tip. Every cell is as wide/tall as the widest/tallest
    block assigned to it, and MAP's job is to keep neighbours relevant: power next to the
    controller it feeds, the controller in the middle with its peripherals around it, and
    the modem/RF bulk on its own row instead of crowding the MCU.
    """
    unknown = sorted(set(dumps) - set(MAP))
    if unknown:
        raise SystemExit(f"MAP has no cell for {', '.join(unknown)} - add them to MAP")
    over = sorted(n for n in dumps if len(BLOCK_META[n][1]) > NOTES_MAX)
    if over:
        raise SystemExit(f"{', '.join(over)}: more than {NOTES_MAX} remark lines - the foot "
                         f"band would run into the block below it (see NOTES_MAX)")
    placed = {name: MAP[name] for name in dumps}
    wide, high = defaultdict(float), defaultdict(float)
    for name, (row, col) in placed.items():
        box = dumps[name]["bbox"]
        wide[col] = max(wide[col], box["maxX"] - box["minX"])
        high[row] = max(high[row], box["maxY"] - box["minY"])
    col_x, row_top = {}, {}
    for col in sorted(wide):
        col_x[col] = sum(wide[c] + gap for c in sorted(wide) if c < col)
    for row in sorted(high):
        # row 0 sits at the top, so each further row starts below the previous one.
        row_top[row] = -sum(high[r] + gap for r in sorted(high) if r < row)
    cells = {}
    for name, (row, col) in placed.items():
        box = dumps[name]["bbox"]
        width, high_ = box["maxX"] - box["minX"], box["maxY"] - box["minY"]
        x0, y1 = col_x[col], row_top[row] + high[row]
        cell = {"dx": x0 - box["minX"], "dy": y1 - box["maxY"],
                "w": width, "h": high_,
                # [x0, y0, x1, y1] of the block's own content, and of the amber partition
                # frame drawn around it. The content bbox already contains the block's KiCad
                # title text (importer kept it as page TEXT), so the title band above it is
                # clear of that by construction - the two do not have to be reconciled.
                "cell": [x0, y1 - high_, x0 + width, y1],
                "frame": frame_box([x0, y1 - high_, x0 + width, y1],
                                   len(BLOCK_META[name][1]))}
        cells[name] = cell
    boxes = [c["frame"] for c in cells.values()]
    total = {"minX": min(b[0] for b in boxes), "minY": min(b[1] for b in boxes),
             "maxX": max(b[2] for b in boxes), "maxY": max(b[3] for b in boxes)}
    return cells, total


def foot_h(lines):
    """Height of the remark strip under a block: content edge down to the frame line."""
    return NOTE_TOP_GAP + max(lines - 1, 0) * NOTE_LINE + NOTE_FS + NOTE_BOTTOM_GAP


def frame_box(cell, lines):
    """The partition frame around one block: content + side padding + title band + remarks.

    [x0, y0, x1, y1], same convention as `cell`. The block's own KiCad title text is already
    inside its content bbox (the importer kept sheet names as page TEXT), so the title band
    above the box cannot collide with it - which is also why no per-block text lifting was
    needed here.
    """
    x0, y0, x1, y1 = cell
    return [x0 - FRAME_PAD, y0 - foot_h(lines), x1 + FRAME_PAD, y1 + TITLE_BAND]


def items(dump, dx, dy):
    """Turn one page's states into create() arguments, shifted onto its tile.

    Components split over three routes because the client treats them as three different
    things, all measured on 2026-09-21 against this project:
      part  - `sch_PrimitiveComponent.create()` needs the OWNING library uuid. For a project
              device `getState_Component()` reports `libraryUuid: ""`, and create() with that
              hangs for minutes without producing a primitive; the project uuid works (~0.2s).
              The designator then comes back through `modify()`, which is what the source page
              shows. Names are only re-applied when the page differs from the device name.
      port  - `createNetPort()`. A netport is a system Netport symbol, not a device: creating
              one from the imported per-net project device comes out as a pinless `part` with
              no net, which would poison the netlist. Every imported port is bidirectional
              (they all came off KiCad hierarchical labels), so `BI` is not a guess.
      flag  - `createNetFlag('Power', ...)`, same reasoning as the port: the two flags are the
              generic power symbols the importer generated.
    """
    parts, ports, flags = [], [], []
    for c in dump["components"]:
        kind = c["ComponentType"]
        if kind in SKIP:
            continue
        x, y = c["X"] + dx, c["Y"] + dy
        common = {"x": x, "y": y, "rotation": c["Rotation"] or 0, "mirror": bool(c["Mirror"])}
        if kind == "netport":
            ports.append(dict(k="port", label=c["Net"], direction="BI", net=c["Net"], **common))
        elif kind == "netflag":
            flags.append(dict(k="flag", label=c["Net"], identification="Power", net=c["Net"],
                              **common))
        else:
            component = c["Component"] or {}
            designator = c["Designator"] if re.match(r"^[A-Z]+\d+$", c["Designator"] or "") else None
            name = c["Name"] if c["Name"] and c["Name"] != component.get("name") else None
            parts.append(dict(k="part", label=designator or c["Name"], uuid=component.get("uuid"),
                            subPartName=c["SubPartName"] or "",
                            # NOT a copy of the source flag: this sheet is a READING VIEW. The
                            # nine source pages already carry every designator, and 嘉立创's
                            # schematic->PCB netlist / BOM export aggregate the whole schematic
                            # document, so a second copy that is "in PCB" would double every ref.
                            # The merge tool therefore always excludes what it places; attrs()
                            # reads the two flags back so the exclusion cannot silently regress.
                            addIntoBom=False, addIntoPcb=False,
                            designator=designator, name=name, **common))
    out = parts
    for t in dump["texts"]:
        out.append({"k": "text", "label": t["Content"][:40], "x": t["X"] + dx, "y": t["Y"] + dy,
                    "content": t["Content"], "rotation": t["Rotation"] or 0,
                    "textColor": t["TextColor"], "fontName": t["FontName"],
                    "fontSize": t["FontSize"], "bold": bool(t["Bold"]),
                    "italic": bool(t["Italic"]), "underLine": bool(t["UnderLine"]),
                    "alignMode": t["AlignMode"]})
    for p in dump["polys"]:
        out.append({"k": "poly", "label": "", "line": shift(p["Line"], dx, dy),
                    "color": p["Color"], "fillColor": p["FillColor"],
                    "lineWidth": p["LineWidth"], "lineType": p["LineType"]})
    for w in dump["wires"]:
        out.append({"k": "wire", "label": w["Net"] or "", "line": shift(w["Line"], dx, dy),
                    "net": w["Net"] or "", "color": w["Color"], "lineWidth": w["LineWidth"],
                    "lineType": w["LineType"]})
    # Each wire is followed by a save(): sch_PrimitiveWire.create() leaves the editor holding
    # the previous wire, and the next create() then throws "create failed!" - measured as a
    # strict alternating pass/fail run (y=1000 ok, 1015 fail, 1030 ok, 1045 fail). Components,
    # texts and polygons do not need it.
    #
    # ports after wires: the system Netport-BI symbol is taller than the 15-unit pitch the
    # imported ports sit on, so a port body overlaps its neighbours' wires and create()
    # refuses a wire whose end lands inside a foreign-net port. Drawn the other way round
    # everything lands, and a wire (which carries its net as data) is worth more than a
    # port that fails to place.
    return out + ports + flags


def shift(line, dx, dy):
    return [v + (dx if i % 2 == 0 else dy) for i, v in enumerate(line)]


def rect(box, line_width, color, label):
    """One rectangle from [x0, y0, x1, y_top], in the client's own terms.

    The client re-derives a rectangle's size from corners snapped to a 0.1-unit grid -
    measured 2026-09-21: a request for (5176.51182, -2301.771655, 1776.0407666, 1662.779525)
    reads back as (5176.5, -2301.8, 1776.1, 1662.8), i.e. width = round(x1,1) - round(x0,1).
    Asking in that same grid is what makes diff() recognise its own work; asking in exact
    units leaves a 0.06 delta, and diff() then treats the frame as missing and stacks a
    second one on top. Texts and wires are stored at full precision, so only this helper
    needs the treatment.
    """
    x0, y0, x1, y1 = (round(v, 1) for v in box)
    return {"k": "rect", "label": label,
            "box": [x0, y1, round(x1 - x0, 1), round(y1 - y0, 1)],
            "lineWidth": line_width, "color": color}


def text(x, y, content, size, align, label, color=None, bold=False):
    """A text anchored at (x, y); align is ESCH_PrimitiveTextAlignMode (1=LEFT_TOP … 9=RIGHT_BOTTOM)."""
    return {"k": "text", "label": label, "x": x, "y": y, "content": content, "rotation": 0,
            "textColor": color, "fontName": None, "fontSize": size, "bold": bold,
            "italic": False, "underLine": False, "alignMode": align}


def decorations(cells, total, stats):
    """Everything that makes the sheet readable rather than just correct: the border, the
    per-block amber partition frames, their titles and remarks, and the title block.

    The page keeps *no* library `sheet` symbol. The importer had put an A4 frame (1170 x 825)
    on every page no matter how much A2-sized content it had already drawn, so on the merged
    sheet the inherited frame is the thing that "leaks": 6930 x 5254 of circuitry inside a
    1170-wide box. No library frame is big enough either (largest available: A0 4676 x 3304),
    which is why the border is drawn from rectangles - and why the page no longer claims a
    paper size, which the user accepted as the trade for one readable sheet.
    """
    x0, y0, x1, y1 = total["minX"], total["minY"], total["maxX"], total["maxY"]
    border = [x0 - MARGIN, y0 - MARGIN - TB_SIDE - TB_H, x1 + MARGIN, y1 + MARGIN]
    inner = [border[0] + INNER_INSET, border[1] + INNER_INSET,
             border[2] - INNER_INSET, border[3] - INNER_INSET]
    out = [rect(border, BORDER_W, INK, "border"),
           rect(inner, INNER_W, INK, "border-inner"),
           text(inner[0] + 60, inner[3] - 25, "AIOT-WATCH · 单页总图 10_ALL", BANNER_FS, 1,
                "banner")]
    for name in sorted(cells):
        cell, (title, notes) = cells[name], BLOCK_META[name]
        fx0, _, fx1, fy1 = cell["frame"]
        cx0, cy0 = cell["cell"][0], cell["cell"][1]
        out.append(rect(cell["frame"], FRAME_W, PART_INK, f"frame:{name}"))
        # Centred in the band between the frame's top line and the block's own content; the
        # KiCad title text that came with the block stays inside that content box, so the two
        # are 60+ units apart and neither repeats the other.
        out.append(text((fx0 + fx1) / 2, fy1 - TITLE_TOP_GAP - TITLE_FS, title, TITLE_FS, 4,
                        f"title:{name}", color=PART_INK, bold=True))
        for n, note in enumerate(notes):
            out.append(text(cx0 - FRAME_PAD + NOTE_X, cy0 - NOTE_TOP_GAP - n * NOTE_LINE,
                            note, NOTE_FS, 1, f"note:{name}:{n}"))
    tb = [inner[2] - TB_W, inner[1] + 55, inner[2] - 55, inner[1] + 55 + TB_H]
    out.append(rect(tb, BLOCK_W, INK, "title-block"))
    lines = [
        ("AIoT 老人看护手表 · 硬件单页总图", 45, True),
        (f"工程 aiot-kicad-import（嘉立创EDA专业版）　页 10_ALL 合并阅读视图　"
         f"版本 EVT-V1 REVIEW DRAFT　{SHEET_DATE}", 28, False),
        (f"内容来自 hardware/kicad 的 KiCad 工程导入　位号 {stats['refs']}　本页网络 "
         f"{stats['nets']}　同名网络已在页内自动相连", 28, False),
        ("发布闸门 HOLD：未布板、不出 Gerber —— NOT FOR FABRICATION", 32, True),
        (f"未选型：{stats['blocked_part']} 个器件 无引脚/无厂牌、{stats['blocked_value']} 项 "
         f"仅待定值，见 JLC_PART_MAP.csv", 28, False),
        ("连通性闸门 tools/check_sch_netlist_parity.py --page 10_ALL，"
         "证据 build/sch_netlist_parity_10_ALL.txt", 28, False),
        ("本页位号已全部排除出 BOM 与 PCB 转交，网表与 BOM 只取 00–08 九个源页", 28, False),
    ]
    y = tb[3] - 55
    for n, (content, size, bold) in enumerate(lines):
        out.append(text(tb[0] + 55, y, content, size, 1, f"tb:{n}", bold=bold))
        y -= size + 25
    legend = [
        "图例：琥珀色框 = 功能分区（00–08 各一块），该区的备注写在框内下方",
        "版面按信号流排布：上排 电源 → 主控 → 显示，中排 4G 模组 / 音频 / IMU·RTC，"
        "下排 触觉按键 / 调试 / 索引",
        "本页把九张功能页整块搬来（块内几何未动），不是逐器件重新走线的真·重排",
        "符号↔封装的绑定状态与每块未定项：见 hardware/jlc/README.md",
        "U2 SIM8230C 未选型 → 符号无引脚，它的连接不在这张图上",
    ]
    y = tb[3] - 55
    for n, content in enumerate(legend):
        out.append(text(inner[0] + 60, y, content, 28, 1, f"legend:{n}"))
        y -= 28 + 25
    return out


# VERIFY's reply buckets -> the item kind each record represents. `frame` is the imported
# page-frame symbol: nothing on the generated sheet may be one (see KEEP_FRAME), so every
# record in that bucket shows up as a stray and gets deleted.
LIVE = {"parts": "part", "ports": "port", "flags": "flag", "frames": "frame",
        "wires": "wire", "texts": "text", "polys": "poly", "rects": "rect"}

# Which delete() call reclaims a record the source pages never asked for. Components,
# net ports, net flags and page frames all live in the same module.
DROP = {"part": "drop_component", "port": "drop_component", "flag": "drop_component",
        "frame": "drop_component", "wire": "drop_wire", "text": "drop_text",
        "poly": "drop_poly", "rect": "drop_rect"}


def shape_of(rec):
    """The comparable footprint of a primitive: its anchor, a line's vertices, a box."""
    for key in ("line", "box"):
        if rec.get(key) is not None:
            return tuple(rec[key])
    return (rec["x"], rec["y"])


def sig_of(kind, rec):
    """`sig()` for a live record, so the two sides of the sheet can be compared."""
    return (kind,) + tuple(round(v, 2) for v in shape_of(rec)[:2])


def sig(item):
    """Stable id for one expected primitive, used to remember which ones hung the client."""
    return sig_of(item["k"], item)


def attrs(item, rec):
    """Non-geometry fields that must still read what the source page says."""
    bad = []
    if item["k"] == "part":
        if item.get("designator") and (rec.get("designator") or "") != item["designator"]:
            bad.append(("designator", item["designator"], rec.get("designator")))
        if item.get("name") and (rec.get("name") or "") != item["name"]:
            bad.append(("name", item["name"], rec.get("name")))
        for field, key in (("addIntoBom", "bom"), ("addIntoPcb", "pcb")):
            if bool(rec.get(key)) != item[field]:
                bad.append((field, item[field], rec.get(key)))
    elif item["k"] in ("port", "flag", "wire"):
        if (rec.get("net") or "") != (item.get("net") or ""):
            bad.append(("net", item.get("net"), rec.get("net")))
    return bad


def diff(expected, verdict, tol=0.05):
    """Compare what the sheet must hold against what the live client reports.

    Presence is decided on geometry within `tol`, never on an exact float match: the
    client stores e.g. -482.71653000000015 where this tool computed -482.71653, and
    re-creating something that is already on the sheet would put a second copy of a
    designator on the page - which breaks the netlist and the BOM. Texts also need an
    identical content string, since two notes can share an anchor.

    Returns (missing items to create, [(item, live record, [bad attrs])] to repair,
    [live records nothing asked for] = duplicates/leftovers).
    """
    grid = defaultdict(list)
    for bucket, kind in LIVE.items():
        for rec in verdict[bucket]:
            shape = shape_of(rec)
            grid[(kind, int(shape[0] // 1), int(shape[1] // 1))].append((rec, shape))
    taken, missing, repairs = set(), [], []
    for item in expected:
        shape = shape_of(item)
        cx, cy = int(shape[0] // 1), int(shape[1] // 1)
        hit = None
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for rec, live_shape in grid.get((item["k"], gx, gy), ()):
                    if id(rec) in taken or len(live_shape) != len(shape):
                        continue
                    if item["k"] == "text" and (rec.get("content") or "") != item["content"]:
                        continue
                    if all(abs(a - b) <= tol for a, b in zip(shape, live_shape)):
                        hit = rec
                        break
                if hit:
                    break
            if hit:
                break
        if hit is None:
            missing.append(item)
            continue
        taken.add(id(hit))
        bad = attrs(item, hit)
        if bad:
            repairs.append((item, hit, bad))
    stray = [(kind, rec) for bucket, kind in LIVE.items() for rec in verdict[bucket]
             if id(rec) not in taken]
    return missing, repairs, stray


def strays_to_items(stray):
    """Delete everything the sheet holds that the source pages did not ask for.

    Two ways the sheet grows junk, both measured on 2026-09-21: a refused
    `sch_PrimitiveWire.create()` still leaves a zero-length, net-less stub at the intended
    start point, and a batch whose request timed out has usually written its primitives
    anyway - so retrying it produces a second `C701` on the same spot. Both then make the
    next create() refuse. `10_ALL` is generated output, so un-asked-for geometry is
    deletable; the nine source pages are where anything real lives.
    """
    out = []
    for kind, rec in stray:
        shape = shape_of(rec)
        label = (rec.get("designator") or rec.get("net") or rec.get("content")
                 or " ".join(f"{v:.0f}" for v in shape[:2]))
        out.append({"k": DROP[kind], "id": rec["id"], "label": f"{kind}:{label}"})
    return out


def repairs_to_items(repairs):
    """Turn attribute mismatches into work items.

    Parts and wires carry their attributes through modify(). Net ports and net flags do
    not - `SCH_PrimitiveComponent.modify()` has no `net` property - so those get deleted
    and re-created by the next round, which is the only route that lands the right net.
    """
    out = []
    for item, rec, bad in repairs:
        if item["k"] == "part":
            prop = {}
            for field, want, _ in bad:
                prop[field] = want
            out.append({"k": "fix_part", "id": rec["id"], "prop": prop,
                        "label": item["label"]})
        elif item["k"] == "wire":
            out.append({"k": "fix_wire", "id": rec["id"], "net": item["net"],
                        "label": item["label"]})
        else:
            out.append({"k": "drop_component", "id": rec["id"], "label": item["label"]})
    return out


def still_missing(items, args):
    """Re-read the sheet and keep only the items that are genuinely not on it.

    Called after a hung request: the bridge gives up at 30s but the client keeps working,
    so the batch may have landed in full, in part, or not at all. Retrying it blind is how
    duplicate designators get made.
    """
    live = execute(VERIFY)
    missing, _, _ = diff(items, live, args.tol)
    return missing


def place(items, project, args, poison, creates=True):
    """Send a queue in batches.

    `creates=True` means every item is geometry-bearing, so a hung batch can be filtered
    against the live sheet (still_missing) and only what failed gets retried.
    Deletes and attribute fixes have no geometry to match on, so there a hang simply ends
    the round - the next verify pass recomputes both lists from scratch.
    """
    for start in range(0, len(items), args.chunk):
        batch = items[start:start + args.chunk]
        for position, item in enumerate(batch):
            item["i"] = position
            item.setdefault("label", item.get("k"))
        tick = time.time()
        try:
            reply = execute(CREATE.replace("__PROJECT__", json.dumps(project))
                            .replace("__ITEMS__", json.dumps(batch, ensure_ascii=False))
                            .replace("__STOP__", str(args.stop_after)))
        except RuntimeError as err:
            print(f"      HUNG on {len(batch)} item(s) ({batch[0]['k']} {batch[0]['label']}…): "
                  f"{str(err)[:90]}", file=sys.stderr)
            time.sleep(args.pause * 5)
            if not creates:
                return False                      # let the next round re-derive the queue
            survivors = still_missing(batch, args)
            if len(survivors) < len(batch):
                print(f"      {len(batch) - len(survivors)} of them landed anyway; "
                      f"retrying {len(survivors)}", file=sys.stderr)
                if survivors and not place(survivors, project, args, poison):
                    return False
            elif len(batch) > 1:
                mid = len(batch) // 2
                if not (place(batch[:mid], project, args, poison)
                        and place(batch[mid:], project, args, poison)):
                    return False
            else:
                signature = sig(batch[0])
                poison[signature] = poison.get(signature, 0) + 1
                print(f"      POISON x{poison[signature]}: {batch[0]['k']} "
                      f"{batch[0]['label']} - nothing landed, nothing on that slot",
                      file=sys.stderr)
            continue
        counts = " ".join(f"{k}={v}" for k, v in sorted(reply["made"].items()))
        print(f"    {len(batch):>3} item(s) in {time.time() - tick:>4.1f}s  {counts}",
              file=sys.stderr)
        for _, kind, label, message in reply["failed"]:
            # informational only: create() has been observed returning falsy for a
            # primitive that did land, so this is never the verdict - diff() is.
            print(f"      refused (verify decides): {kind} {label}: {message}",
                  file=sys.stderr)
        time.sleep(args.pause)
    return True


def in_tile(rec, cell):
    x0, y0, x1, y1 = cell["cell"]
    return x0 - 1 <= rec["x"] <= x1 + 1 and y0 - 1 <= rec["y"] <= y1 + 1


def plan_round(expected, missing, stray, live, cells, purge=True):
    """Order one round's work so a retried wire is not refused by its own net port.

    Measured on 2026-09-21: `sch_PrimitiveWire.create()` refuses outright while a net port
    stands on either of the intended endpoints - delete the port and the same five wires
    that had been refused for three rounds all land first try. Within a tile that never
    bites, because items() already draws wires before ports; it is the *retry* rounds that
    walk into it, by which time the port is up. So the ports standing on a missing wire's
    endpoints come down first and go back up after the wire is drawn - only those, since
    each one costs a delete plus a create and a tile carries 40-90 of them.
    """
    tips = defaultdict(list)
    for item in missing:
        if item["k"] != "wire":
            continue
        line = item["line"]
        tips[item.get("tile")].extend([(line[0], line[1]), (line[2], line[3])])
    blocking = []
    for bucket, kind in (("ports", "port"), ("flags", "flag")):
        for rec in live[bucket]:
            for name, points in tips.items():
                if not in_tile(rec, cells[name]):
                    continue
                if any(abs(rec["x"] - px) <= 2 and abs(rec["y"] - py) <= 2
                       for px, py in points):
                    blocking.append((kind, rec))
                    break
    dirty = {name for name in tips if any(
        in_tile(rec, cells[name]) for _, rec in blocking)}
    drops = (strays_to_items(stray) if purge else []) + [
        {"k": DROP[kind], "id": rec["id"],
         "label": f"{kind}:{rec.get('net')}@{rec['x']:.0f},{rec['y']:.0f}"}
        for kind, rec in blocking]
    # Only a port that is really being deleted, or that never landed, may be erected again:
    # a second copy on the same tip would double the net it carries.
    doomed = {sig_of(kind, rec) for kind, rec in blocking}
    gone = {sig(item) for item in missing}
    refresh = [item for item in expected if item["k"] in ("port", "flag")
               and item.get("tile") in dirty and (sig(item) in doomed or sig(item) in gone)]
    relit = {sig(item) for item in refresh}
    creates = [item for item in missing if item["k"] not in ("port", "flag")]
    creates += [item for item in missing
                if item["k"] in ("port", "flag") and sig(item) not in relit]
    creates += refresh
    return drops, creates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="", help="comma-separated subset, e.g. 05_DISPLAY")
    ap.add_argument("--read-only", action="store_true", help="dump page states, write nothing")
    ap.add_argument("--refresh", action="store_true",
                    help="re-read the source pages instead of reusing build/merge/*.json")
    ap.add_argument("--incremental", action="store_true",
                    help="keep what is already on the sheet and only place what is missing")
    ap.add_argument("--chunk", type=int, default=12, help="primitives per bridge request")
    ap.add_argument("--pause", type=float, default=1.0,
                    help="seconds to let the client settle between requests - it refuses "
                         "creates while it is still catching up with the last batch")
    ap.add_argument("--rounds", type=int, default=6,
                    help="verify->place->verify passes before giving up")
    ap.add_argument("--max-hangs", type=int, default=2, dest="max_hangs",
                    help="drop a primitive from the merge after this many client hangs")
    ap.add_argument("--stop-after", type=int, default=3, dest="stop_after",
                    help="abandon a batch after this many consecutive refusals")
    ap.add_argument("--tol", type=float, default=0.05,
                    help="how close a live primitive must sit to count as the expected one")
    ap.add_argument("--no-purge", action="store_true",
                    help="report junk on the sheet instead of deleting it")
    ap.add_argument("--gap", type=float, default=GAP)
    ap.add_argument("--target", default="",
                    help="page to build (default 10_ALL). Use a scratch name to rebuild the "
                         "sheet in a fresh page when the current one has rot the API cannot "
                         "reach - the client exports primitives it no longer lists.")
    args = ap.parse_args()
    global TARGET_NAME
    if args.target:
        TARGET_NAME = args.target

    project = execute("return (await eda.dmt_Project.getCurrentProjectInfo()).uuid;")
    pages = page_records()
    target = execute(ENSURE_TARGET.replace("__NAME__", json.dumps(TARGET_NAME)))
    print(f"project {project} / target page {TARGET_NAME}: {target['uuid']} "
          f"({'created' if target['created'] else 'reused'}, {target['pages']} pages total)",
          file=sys.stderr)
    names = [p["name"] for p in pages
             if SOURCE.match(p["name"]) and p["uuid"] != target["uuid"]]
    if args.pages:
        wanted = {x.strip() for x in args.pages.split(",") if x.strip()}
        missing_names = wanted - set(names)
        if missing_names:
            raise SystemExit(f"unknown page(s): {', '.join(sorted(missing_names))} - "
                             f"have: {', '.join(names)}")
        names = [n for n in names if n in wanted]
        print(f"WARNING: subset run - the sheet is wiped first, so {TARGET_NAME} ends up "
              f"holding only {', '.join(names)}. Finish with a full run.", file=sys.stderr)

    if args.refresh:
        for name in names:
            path = MERGE / f"{name}.json"
            if path.exists():
                path.unlink()
    dumps = read_pages(names)
    if args.read_only:
        return 0
    cells, total = layout(dumps, args.gap)
    layout_doc = {"target": target["uuid"], "cells": cells, "total": total}
    LAYOUT.write_text(json.dumps(layout_doc, ensure_ascii=False, indent=1))
    expected = []
    for name in names:
        cell = cells[name]
        tile_items = items(dumps[name], cell["dx"], cell["dy"])
        for item in tile_items:
            item["tile"] = name
        expected.extend(tile_items)
    # Numbers quoted on the sheet are counted from what is actually being merged, never
    # copied out of a document that could have drifted.
    stats = {
        "refs": len({i["designator"] for i in expected
                     if i["k"] == "part" and i.get("designator")}),
        "nets": len({i["net"] for i in expected if i["k"] in ("port", "flag", "wire")
                     and i.get("net")}),
    }
    part_map = HERE.parent / "JLC_PART_MAP.csv"
    if part_map.exists():
        tiers = [row["Tier"] for row in csv.DictReader(part_map.open())]
        stats["blocked_part"] = tiers.count("BLOCKED_PART")
        stats["blocked_value"] = tiers.count("BLOCKED_VALUE")
    else:
        print(f"WARNING: {part_map} missing - the title block's 未选型 counts are 0",
              file=sys.stderr)
        stats["blocked_part"] = stats["blocked_value"] = 0
    expected.extend(decorations(cells, total, stats))
    want = defaultdict(int)
    for item in expected:
        want[item["k"]] += 1
    print(f"tiles: {len(cells)}  framed extent: "
          f"{total['maxX'] - total['minX']:.1f} x {total['maxY'] - total['minY']:.1f} API units "
          f"(border adds {2 * MARGIN + TB_SIDE + TB_H:.0f} more height)", file=sys.stderr)
    print("expected: " + " ".join(f"{k}={want[k]}" for k in sorted(want))
          + f" total={len(expected)}", file=sys.stderr)
    print("stats: " + " ".join(f"{k}={v}" for k, v in sorted(stats.items())), file=sys.stderr)

    if not args.incremental:
        gone = execute(RESET.replace("__TARGET__", json.dumps(target["uuid"]))
                       .replace("__KEEP__", json.dumps("sheet" if KEEP_FRAME else "")))
        print("reset: " + json.dumps(gone["gone"], ensure_ascii=False), file=sys.stderr)
    execute(OPEN.replace("__TARGET__", json.dumps(target["uuid"])))

    poison = {}
    verdict_state = None
    for round_no in range(1, args.rounds + 2):
        live = execute(VERIFY)
        missing, repairs, stray = diff(expected, live, args.tol)
        blocked_sig = {sig(it) for it in missing if poison.get(sig(it), 0) >= args.max_hangs}
        blocked = [it for it in missing if sig(it) in blocked_sig]
        missing = [it for it in missing if sig(it) not in blocked_sig]
        counts = {LIVE[b]: len(live[b]) for b in LIVE}
        print(f"round {round_no}: live " + " ".join(f"{k}={counts[k]}" for k in sorted(counts))
              + f" | missing={len(missing)} blocked={len(blocked)} repair={len(repairs)} "
              f"stray={len(stray)}", file=sys.stderr)
        for item, rec, bad in repairs[:10]:
            print(f"      {item['k']} {item['label']} ({rec['id']}): "
                  + ", ".join(f"{f}!={a}" for f, e, a in bad), file=sys.stderr)
        for item in missing[:10]:
            print(f"      still missing: {item['k']} {item['label']}", file=sys.stderr)
        if not missing and not repairs and not stray:
            verdict_state = (missing, repairs, stray, blocked, live)
            break
        if round_no == args.rounds + 1:
            verdict_state = (missing, repairs, stray, blocked, live)
            break
        drops, creates = plan_round(expected, missing, stray, live, cells,
                                    purge=not args.no_purge)
        print(f"      plan: {len(drops)} delete, {len(creates)} create", file=sys.stderr)
        place(repairs_to_items(repairs) + drops, project, args, poison, creates=False)
        place(creates, project, args, poison)

    missing, repairs, stray, blocked, live = verdict_state
    if blocked:
        print(f"NEVER PLACED (the client hung on these {args.max_hangs}x): "
              + ", ".join(f"{it['k']} {it['label']}" for it in blocked), file=sys.stderr)
    for kind, rec in stray[:20]:
        print(f"      STRAY on the sheet ({kind}): {shape_of(rec)} net={rec.get('net')} "
              f"name={rec.get('name') or rec.get('content')} id={rec['id']}", file=sys.stderr)
    for item, rec, bad in repairs[:20]:
        print(f"      WRONG ATTR {item['k']} {item['label']}: "
              + ", ".join(f"{f}!={a}" for f, e, a in bad), file=sys.stderr)
    counts = {LIVE[b]: len(live[b]) for b in LIVE}
    hard = len(missing) + len(repairs) + len(stray) + len(blocked)
    print(f"\n{'PASS' if hard == 0 else 'FAIL'}: {len(expected)} primitive(s) expected, live "
          + " ".join(f"{k}={counts[k]}" for k in sorted(counts))
          + f"; missing={len(missing)} blocked={len(blocked)} "
          f"attr-repair={len(repairs)} stray={len(stray)}", file=sys.stderr)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
