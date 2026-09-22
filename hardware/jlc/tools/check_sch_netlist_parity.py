#!/usr/bin/env python3
"""Rebuild the schematic's netlist through the live client and diff it against KiCad.

This is the phase-1 acceptance gate for connectivity: it proves that what the
嘉立创EDA project actually holds matches `hardware/kicad/docs/aiot-watch.net.xml`
ref-by-ref and pin-by-pin. It also settles whether the importer's float debris on
wire endpoints (see tools/scan_wire_pin_offsets.py) has cost us any connection -
if a pin's net is missing or wrong here, the gap was real.

Resolution model (read off the live document, not off geometry alone):
    a pin tip carries the NET of every wire endpoint sitting on it, plus the NET
    of every `componentType === 'netport'` symbol sitting on it. Wires and
    netports both store their net as data, so this is what the tool reports even
    where the two primitives touch with a 1e-13 sliver.

Refs that KiCad knows but the JLC project has no pin for are reported as MISSING
(never invented); pins the JLC project carries without a KiCad entry are EXTRA.

Two categories are expected deltas, not defects, and are listed on their own:
    no-connect  - KiCad names these `unconnected-(...)`. The JLC side must be
                  empty; a real net there would mean a pin KiCad left floating
                  got wired in.
    renamed     - the pad-numbering decisions taken during footprint binding: U5's
                  and U6's exposed pad moved from `EP` to the datasheet numbers
                  9 / 17, and U9 gained pin 21 for its die-attach pad.

    python3 hardware/jlc/tools/check_sch_netlist_parity.py
    python3 hardware/jlc/tools/check_sch_netlist_parity.py --ref U9 --verbose

    # the generated single-sheet summary must pass the same gate on its own:
    python3 hardware/jlc/tools/check_sch_netlist_parity.py --page 10_ALL
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402

BUILD = HERE.parent / "build"
NETLIST = HERE.parent.parent / "kicad" / "docs" / "aiot-watch.net.xml"
EVIDENCE = BUILD / "sch_netlist_parity.txt"
# tools/merge_schematic_pages.py's output: a single-sheet reading view that repeats every
# designator from the functional pages.
MERGED_PAGE = "10_ALL"

# KiCad names a floating pin's net `unconnected-(REF-PinN)`; nothing on the JLC
# side is supposed to match it, so it needs its own verdict.
UNCONNECTED = re.compile(r"^unconnected-\(")

# Pad-numbering deltas approved while binding LCSC footprints: the exposed pads
# were renumbered from KiCad's `EP` to the datasheet/LCSC numbers.
RENAMED = {"U5.EP": "U5.9", "U6.EP": "U6.17"}
# The ES8311 die-attach pad: absent from KiCad's 20-pin symbol, added on the
# strength of the datasheet's reference circuit (Rev 5.0 §3, `21 / PGND`).
ADDED = {"U9.21": "GND"}

PAGES = """
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return pages.map(p => ({uuid: p.uuid, name: p.title || p.name || p.friendlyName || ''}));
"""

PAYLOAD = """
await eda.dmt_EditorControl.openDocument(__PAGE__);
const comps = await eda.sch_PrimitiveComponent.getAll();
const wires = await eda.sch_PrimitiveWire.getAll();
const segs = wires.map(w => ({net: w.getState_Net() || '', line: w.getState_Line()}));
const ports = [];
const parts = [];
for (const c of comps) {
    const desig = c.getState_Designator() || '';
    if (!/^[A-Z]+[0-9]+$/.test(desig)) {
        for (const p of await c.getAllPins()) {
            if (c.getState_ComponentType() === 'netport' || c.getState_Net())
                ports.push({x: p.x, y: p.y, net: c.getState_Net() || c.getState_Name() || ''});
        }
        continue;
    }
    parts.push({ref: desig, pins: await c.getAllPins()});
}
const tol = __TOL__;
const hits = (x, y) => {
    const nets = [], offsets = [];
    for (const s of segs) {
        const d = Math.min(Math.hypot(s.line[0] - x, s.line[1] - y),
                           Math.hypot(s.line[2] - x, s.line[3] - y));
        if (d < tol) { nets.push(s.net); offsets.push(d); }
    }
    for (const p of ports) {
        const d = Math.hypot(p.x - x, p.y - y);
        if (d < tol) { nets.push(p.net); offsets.push(d); }
    }
    return {nets: [...new Set(nets)].filter(Boolean).sort(), worst: Math.max.apply(null, offsets.concat([0]))};
};
return {page: __PAGE__, parts: parts.map(part => ({ref: part.ref,
    pins: part.pins.map(p => {
        const h = hits(p.x, p.y);
        return {pin: String(p.pinNumber), name: p.pinName, net: h.nets, off: h.worst,
                nc: !!p.noConnected};
    })}))};
"""


def kicad_netlist():
    """ref.pin -> net name, straight out of the KiCad netlist file."""
    xml = NETLIST.read_text()
    try:
        body = xml.split("<nets>", 1)[1].split("</nets>", 1)[0]
    except IndexError as err:
        raise SystemExit(f"{NETLIST} has no <nets> section ({err})") from None
    out = {}
    for match in re.finditer(r'<net code="\d+" name="([^"]+)"[^>]*>(.*?)</net>', body, re.S):
        net, block = match.groups()
        for ref, pin in re.findall(r'<node ref="([^"]+)" pin="([^"]+)"', block):
            out[f"{ref}.{pin}"] = net
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=0.01, help="touch tolerance, API units")
    ap.add_argument("--ref", default="", help="restrict the diff to one designator")
    ap.add_argument("--page", default="",
                    help="scan only this sheet (e.g. 10_ALL, so the merged page has to "
                         "carry the whole netlist by itself)")
    ap.add_argument("--verbose", action="store_true", help="list matching pins too")
    ap.add_argument("--include-merged", action="store_true", dest="include_merged",
                    help=f"also scan {MERGED_PAGE} in an all-pages run (its refs overwrite "
                         f"the source pages, so this is only for a deliberate comparison)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    # A page-scoped run writes its own evidence file: the all-pages report is the
    # phase-1 record and must not be replaced by a single-sheet check.
    if args.out is None:
        args.out = str(EVIDENCE if not args.page
                       else EVIDENCE.with_name(f"{EVIDENCE.stem}_{args.page}.txt"))

    expect = kicad_netlist()
    if not expect:
        raise SystemExit(f"no nets parsed from {NETLIST}")

    got = {}
    offsets = defaultdict(int)
    conflicts = []
    lines = []
    pages = execute(PAGES)
    if args.page:
        picked = [p for p in pages if p["name"] == args.page]
        if not picked:
            raise SystemExit(f"no page named {args.page} - have: "
                             + ", ".join(p["name"] for p in pages))
        pages = picked
    elif not args.include_merged:
        # `10_ALL` is generated reading material: it repeats all 126 designators, and this
        # tool keys results by ref.pin, so scanning it alongside the source pages would let
        # one copy silently overwrite the other. Check it on its own with --page 10_ALL.
        pages = [p for p in pages if p["name"] != MERGED_PAGE]
    for page in pages:
        code = (PAYLOAD.replace("__PAGE__", json.dumps(page["uuid"]))
                .replace("__TOL__", repr(args.tol)))
        result = execute(code)
        for part in result["parts"]:
            if args.ref and part["ref"] != args.ref:
                continue
            for p in part["pins"]:
                key = f"{part['ref']}.{p['pin']}"
                if len(p["net"]) > 1:
                    conflicts.append((page["name"], key, p["net"]))
                got[key] = {"net": "+".join(p["net"]), "nc": p["nc"], "off": p["off"],
                            "name": p["name"]}
                if p["off"]:
                    offsets[f"{p['off']:.1e}"] += 1
        lines.append(page["name"])
        print(f"{page['name']:<28} parts={len(result['parts'])} "
              f"pins={sum(len(x['pins']) for x in result['parts'])}", file=sys.stderr)

    checked = {k: v for k, v in got.items() if not args.ref or k.startswith(args.ref + ".")}
    scope = [k for k in expect if not args.ref or k.startswith(args.ref + ".")]
    matched, wrong, missing = [], [], []
    nc_ok, nc_wired, renamed_ok = [], [], []
    for key in sorted(scope):
        net = expect[key]
        actual = checked.get(key, {}).get("net", "")
        if UNCONNECTED.match(net):
            (nc_wired if actual else nc_ok).append((key, net, actual))
        elif key not in checked:
            alt = RENAMED.get(key)
            moved = checked.get(alt, {}).get("net", "") if alt else ""
            if alt and moved == net:
                renamed_ok.append((key, alt, net))
            else:
                missing.append((key, net))
        elif actual == net:
            matched.append((key, net, actual))
        else:
            wrong.append((key, net, actual))
    added_ok = sorted(k for k in ADDED if checked.get(k, {}).get("net") == ADDED[k])
    renamed_targets = set(RENAMED.values())
    extra = sorted(k for k in checked if k not in expect and checked[k]["net"]
                   and k not in ADDED and k not in renamed_targets)

    text = [f"tolerance: {args.tol!r}   filter: {args.ref or 'all refs'}",
            f"pages scanned: {len(lines)}", "",
            f"kicad nodes in scope   : {len(scope)}",
            f"jlc pins resolved    : {len(checked)}",
            f"matched              : {len(matched)}",
            f"no-connect open      : {len(nc_ok)}  (WRONG NET on NC pins: "
            f"{len(nc_wired)})",
            f"renumbered pads      : {len(renamed_ok)} of {len(RENAMED)} expected",
            f"added pads           : {len(added_ok)} of {len(ADDED)} expected",
            f"WRONG NET            : {len(wrong)}",
            f"MISSING in jlc       : {len(missing)}",
            f"EXTRA in jlc         : {len(extra)}",
            f"multi-net pins       : {len(conflicts)}", ""]
    if nc_wired:
        text.append("A KI CAD NO-CONNECT PIN CARRIES A NET in the imported project:")
        for key, exp, act in nc_wired:
            text.append(f"  {key:<12} kicad={exp:<18} jlc={act}")
        text.append("")
    if wrong:
        text.append("WRONG NET (both sides have the pin, nets differ):")
        for key, exp, act in wrong:
            text.append(f"  {key:<12} kicad={exp:<18} jlc={act}")
        text.append("")
    if missing:
        text.append("MISSING in jlc (KiCad has the connection, the imported project "
                    "has no such pin - expected for the un-selected refs):")
        by_ref = defaultdict(list)
        for key, net in missing:
            by_ref[key.split(".")[0]].append((key, net))
        for ref in sorted(by_ref):
            text.append(f"  {ref} ({len(by_ref[ref])} node(s)): "
                        + ", ".join(k.split(".", 1)[1] for k, _ in by_ref[ref])
                        + "  [nets: "
                        + ", ".join(sorted({n for _, n in by_ref[ref]})) + "]")
        text.append("")
    if extra:
        text.append("EXTRA in jlc (pin resolved to a net KiCad has no entry for):")
        for key in extra:
            text.append(f"  {key:<12} jlc={checked[key]['net']}")
        text.append("")
    if conflicts:
        text.append("multi-net pins (one tip touching two different net names):")
        for page, key, nets in conflicts:
            text.append(f"  {page:<24} {key:<10} {nets}")
        text.append("")
    if renamed_ok or added_ok:
        text.append("expected deltas from the pad-numbering decisions (verified "
                    "to carry the right net):")
        for old, new, net in renamed_ok:
            text.append(f"  {old:<10} -> {new:<8} {net}")
        for key in added_ok:
            text.append(f"  (added) {key:<8}    {ADDED[key]}")
        text.append("")
    missing_renames = sorted(set(RENAMED) - {old for old, _, _ in renamed_ok})
    if missing_renames:
        text.append("RENAMED pads not found renumbered on the JLC side: "
                     + ", ".join(f"{k}->{RENAMED[k]}" for k in missing_renames))
        text.append("")
    missing_adds = sorted(set(ADDED) - set(added_ok))
    if missing_adds:
        text.append("ADDED pads missing or on the wrong net: "
                     + ", ".join(f"{k}(!={ADDED[k]})" for k in missing_adds))
        text.append("")
    if args.verbose and matched:
        text.append("matched:")
        for key, exp, act in matched:
            text.append(f"  {key:<12} kicad={exp:<18} jlc={act}")
        text.append("")
    text.append(f"pin tips resolved through a non-zero offset "
                f"(float debris, count by magnitude): {dict(sorted(offsets.items()))}")
    report = "\n".join(text) + "\n"
    Path(args.out).write_text(report)
    print(report, end="")
    hard = (len(wrong) + len(extra) + len(conflicts) + len(nc_wired)
            + len(missing_renames) + len(missing_adds))
    print(f"\n{'PASS' if hard == 0 else 'FAIL'}: {hard} defect(s) "
          f"({len(matched)} node(s) matched, {len(nc_ok)} no-connects left open); "
          f"{len(missing)} KiCad node(s) absent from the imported project")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
