#!/usr/bin/env python3
"""Give U9 (ES8311) its exposed die-attach pad as pin 21 and wire it to GND.

The LCSC WQFN-20 land pattern bound onto U9 has 21 pads: 1-20 around the edge
plus a centre pad numbered 21. The imported KiCad symbol stops at 20, so that pad
had no pin to mate with. This appends pin 21 to the project symbol and draws the
wire + GND net port for it on the audio page.

Where the number and the net come from - ES8311 Rev 5.0: the pin table (sec 2)
lists only 1-20, and the package drawing (sec 8) labels the centre pad "EXPOSED
DIE ATTACH PAD" *without a number*. Both the number 21 and its net come from the
typical application circuit (sec 3), which puts "21 / PGND" on the bottom edge
between pins 10 (AGND) and 11 (AVDD) and ties it to the same ground rail. This
board has one ground net, so pin 21 lands on GND next to pins 5, 10 and 20. The
datasheet on file is a third-party mirror marked Confidential - internal review
only, replace it with the official release before any supplier or certification
use.

Geometry is read off the live document instead of being typed in: the new slot
sits MARGIN below the symbol's current bottom edge, the body then grows to
restore that same MARGIN, and the wire runs to the column the neighbouring GND
ports already use. A re-import that shifts the layout still patches correctly.

Primitives cannot be added through the document-source API - updateDocumentSource
takes in-place value edits and rejects every appended record - so creation goes
through the sch_Primitive* API against the open editor plus sch_Document.save().
Source is only written back for the two pure value edits (body edge, field text).
One bridge request per step; each step prints ALREADY once its result is present.

This is a post-import patch: re-run it after every KiCad re-import.

    python3 hardware/jlc/tools/patch_u9_die_pad.py
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402
from patch_symbol_pin import device_attrs  # noqa: E402

REF = "U9"
PAGE_NAME = "06_AUDIO"
TEMPLATE_PIN = "10"     # AGND - last row of the left column; pin 21 clones its shape
NEW_PIN = "21"
NEW_NAME = "PGND"       # the name the datasheet's reference circuit gives the pad
NET = "GND"
PIN_TYPE = "Power"
MARGIN = 15             # gap the existing rows keep from the body edge
TEXT_GAP = 6            # Value sits this far below the body, Designator 12 further

# The `{"type":…}||{body}|` line reader shared by the symbol payloads.
PARSE = """
function parseLine(line) {
    const j = line.indexOf('||');
    if (j < 0) return null;
    try {
        return [JSON.parse(line.slice(0, j)),
                JSON.parse(line.slice(j + 2).replace(/\\|$/, ''))];
    } catch (e) { return null; }
}
function rectEdge(src) {
    for (const line of src.split('\\n')) {
        const r = parseLine(line);
        if (r && r[0].type === 'RECT') return r[1].dotY1;
    }
    return null;
}
"""

ADD_PIN = PARSE + """
const lib = __LIB__, sym = __SYM__;
await eda.lib_Symbol.openInEditor(sym, lib);
const before = await eda.sch_PrimitivePin.getAll();
if (before.some(p => p.getState_PinNumber() === __NEW__))
    return {status: 'ALREADY', pins: before.length};
const tpl = before.find(p => p.getState_PinNumber() === __TPL__);
if (!tpl) throw new Error('template pin ' + __TPL__ + ' not found in symbol ' + sym);
const edge = rectEdge(await eda.sys_FileManager.getDocumentSource());
if (edge === null) throw new Error('symbol ' + sym + ' has no RECT body record');
const y = __MARGIN__ - edge;
const created = await eda.sch_PrimitivePin.create(tpl.getState_X(), y, __NEW__, __NAME__,
    tpl.getState_Rotation(), tpl.getState_PinLength(), null, tpl.getState_PinShape(), __TYPE__);
created.done();
const saved = await eda.sch_Document.save();
const after = await eda.sch_PrimitivePin.getAll();
const mine = after.find(p => p.getState_PinNumber() === __NEW__);
return {status: (saved && mine && after.length === before.length + 1) ? 'PATCHED' : 'FAILED',
    saved: !!saved, pins: after.length, bodyEdge: edge, apiSlotY: y,
    tip: mine ? {x: mine.getState_X(), y: mine.getState_Y(), rotation: mine.getState_Rotation()} : null};
"""

GROW_BODY = PARSE + """
const lib = __LIB__, sym = __SYM__, margin = __MARGIN__, gap = __TEXT__;
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
const recs = src.split('\\n').map(parseLine).filter(Boolean);
const bodies = {};
for (const [h, b] of recs) if (h.type === 'PIN') bodies[h.id] = b;
let pinY = null;
for (const [h, b] of recs) {
    if (h.type === 'ATTR' && b.key === 'Pin Number' && b.value === __NEW__
        && b.parentId in bodies) pinY = bodies[b.parentId].y;
}
if (pinY === null) throw new Error('pin ' + __NEW__ + ' is not in the symbol - run add-pin first');
const edge = rectEdge(src);
const want = pinY - margin;
const texts = {Value: want - gap, Designator: want - gap - 12};
if (edge <= want) return {status: 'ALREADY', bodyEdge: edge, pinSourceY: pinY};
const lines = src.split('\\n');
let hits = 0;
for (let i = 0; i < lines.length; i++) {
    const r = parseLine(lines[i]);
    if (!r) continue;
    let changed = false;
    if (r[0].type === 'RECT' && r[1].dotY1 > want) { r[1].dotY1 = want; changed = true; }
    if (r[0].type === 'ATTR' && r[1].parentId === '1' && r[1].key in texts
        && typeof r[1].y === 'number' && r[1].y > texts[r[1].key]) {
        r[1].y = texts[r[1].key]; changed = true;
    }
    if (!changed) continue;
    lines[i] = lines[i].slice(0, lines[i].indexOf('||')) + '||' + JSON.stringify(r[1]) + '|';
    hits++;
}
const ok = await eda.lib_Symbol.updateDocumentSource(sym, lib, lines.join('\\n'));
const readBack = {bodyEdge: null, text: {}};
for (const r of (await eda.sys_FileManager.getDocumentSource()).split('\\n').map(parseLine)) {
    if (!r) continue;
    if (r[0].type === 'RECT') readBack.bodyEdge = r[1].dotY1;
    if (r[0].type === 'ATTR' && r[1].parentId === '1' && r[1].key in texts)
        readBack.text[r[1].key] = r[1].y;
}
return {status: (ok && readBack.bodyEdge === want) ? 'PATCHED' : 'FAILED',
    rewrote: hits, bodyEdge: want, pinSourceY: pinY, readBack: readBack};
"""

WIRE_ON_PAGE = """
await eda.dmt_EditorControl.openDocument(__PAGE__);
const comps = await eda.sch_PrimitiveComponent.getAll();
const part = comps.find(c => c.getState_Designator() === __REF__);
if (!part) throw new Error(__REF__ + ' is not placed on this page');
const tip = (await part.getAllPins()).find(p => String(p.pinNumber) === __NEW__);
if (!tip) throw new Error('the placed ' + __REF__ + ' has no pin ' + __NEW__
    + ' - close and reopen the page so the symbol change shows through');
const left = comps.filter(c => c.getState_ComponentType() === 'netport'
    && c.getState_Net() === __NET__ && c.getState_X() < tip.x);
if (!left.length) throw new Error('no existing ' + __NET__ + ' net port left of pin ' + __NEW__);
const model = left.reduce((a, b) => Math.abs(a.getState_Y() - tip.y)
    <= Math.abs(b.getState_Y() - tip.y) ? a : b);
const flagX = model.getState_X();
const touches = (l, x, y) => (l[0] === x && l[1] === y) || (l[2] === x && l[3] === y);
const out = {tip: {x: tip.x, y: tip.y}, flagX: flagX};
const wired = (await eda.sch_PrimitiveWire.getAll()).some(w => {
    const l = w.getState_Line();
    return w.getState_Net() === __NET__ && touches(l, tip.x, tip.y)
        && (l[0] === flagX || l[2] === flagX);
});
if (wired) {
    out.wire = 'ALREADY';
} else {
    const w = await eda.sch_PrimitiveWire.create([tip.x, tip.y, flagX, tip.y], __NET__,
        null, 1, 0);
    w.done();
    out.wire = 'created';
}
const ported = comps.some(c => c.getState_ComponentType() === 'netport'
    && c.getState_Net() === __NET__ && c.getState_X() === flagX && c.getState_Y() === tip.y);
if (ported) {
    out.port = 'ALREADY';
} else {
    const f = await eda.sch_PrimitiveComponent.create(model.getState_Component(), flagX,
        tip.y, model.getState_SubPartName(), model.getState_Rotation(), false, true, true);
    f.done();
    out.port = 'created';
}
out.saved = await eda.sch_Document.save();
return out;
"""

PAGES = ("const p = await eda.dmt_Schematic.getAllSchematicPagesInfo();"
         "return p.map(x => ({uuid: x.uuid, name: x.title || x.name || ''}));")


def fill(template, **values):
    code = template
    for key, value in values.items():
        code = code.replace(f"__{key}__", json.dumps(value))
    if "__" in code:
        raise SystemExit("unsubstituted placeholder left in payload:\n" + code)
    return code


def main():
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    project = json.loads((HERE.parent / "build" / "import_kicad.result.json").read_text())["uuid"]
    _, symbol = device_attrs(REF)
    pages = execute(PAGES)
    page = next((p for p in pages if PAGE_NAME in p["name"]), None)
    if not page:
        raise SystemExit(f"page {PAGE_NAME} not found - pages are "
                         f"{', '.join(p['name'] for p in pages)}")
    print(f"{REF}: symbol {symbol}, page {page['name']} ({page['uuid']}), project {project}")

    steps = [
        (f"add pin {NEW_PIN}={NEW_NAME}", fill(
            ADD_PIN, LIB=project, SYM=symbol, NEW=NEW_PIN, TPL=TEMPLATE_PIN,
            NAME=NEW_NAME, TYPE=PIN_TYPE, MARGIN=MARGIN)),
        ("grow symbol body + drop field text", fill(
            GROW_BODY, LIB=project, SYM=symbol, NEW=NEW_PIN, MARGIN=MARGIN, TEXT=TEXT_GAP)),
        (f"wire + {NET} port on {PAGE_NAME}", fill(
            WIRE_ON_PAGE, PAGE=page["uuid"], REF=REF, NEW=NEW_PIN, NET=NET)),
    ]
    for name, code in steps:
        result = execute(code)
        print(f"  {name:<34} {json.dumps(result, ensure_ascii=False)}")
        if isinstance(result, dict) and result.get("status") == "FAILED":
            raise SystemExit(f"step failed: {name}")
    print("verify with:")
    print("  python3 hardware/jlc/tools/check_footprint_pin_parity.py")
    print("  python3 hardware/jlc/tools/check_sch_netlist_parity.py --ref U9")
    return 0


if __name__ == "__main__":
    sys.exit(main())
