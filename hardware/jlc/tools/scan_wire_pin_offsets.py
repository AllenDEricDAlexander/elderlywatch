#!/usr/bin/env python3
"""Scan every schematic page for wires that touch a pin *almost* exactly.

The KiCad -> EasyEDA importer sometimes writes a wire endpoint one float
epsilon away from the pin tip it is meant to join (observed on U9 pins 2/8/12/18:
source y 260.00000000000006 against a pin at 260). This is a scope probe, not a
gate: it answers how much of the design carries that artifact, so the fix can be
sized instead of guessed.

Per pin tip the scan classifies the nearest wire endpoint:
    exact  distance is exactly 0
    loose  0 < distance < --tol (the artifact we are hunting)
    none   nothing that close - normal for pins hanging off a net port/label,
           and for genuinely broken connections, so it is counted but not listed

One bridge request per page; the payload only reads, so re-running is free.

    python3 hardware/jlc/tools/scan_wire_pin_offsets.py
    python3 hardware/jlc/tools/scan_wire_pin_offsets.py --tol 1e-9 --ref U9
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402

BUILD = HERE.parent / "build"
EVIDENCE = BUILD / "wire_pin_offsets.txt"

PAYLOAD = """
await eda.dmt_EditorControl.openDocument(__PAGE__);
const comps = await eda.sch_PrimitiveComponent.getAll();
const wires = await eda.sch_PrimitiveWire.getAll();
const want = __REF__;
const out = {page: __PAGE__, components: comps.length, wires: wires.length,
    scanned: 0, exact: 0, loose: [], none: [], fractionalTips: 0};
for (const c of comps) {
    const desig = c.getState_Designator() || '';
    if (want && desig !== want) continue;
    for (const p of await c.getAllPins()) {
        out.scanned++;
        if (p.x !== Math.round(p.x) || p.y !== Math.round(p.y)) out.fractionalTips++;
        let exactHit = false, nearest = null;
        for (const w of wires) {
            const l = w.getState_Line();
            const d = Math.min(Math.hypot(l[0] - p.x, l[1] - p.y), Math.hypot(l[2] - p.x, l[3] - p.y));
            if (d === 0) { exactHit = true; break; }
            if (nearest === null || d < nearest.d) nearest = {d, net: w.getState_Net()};
        }
        if (exactHit) { out.exact++; continue; }
        if (nearest === null || nearest.d >= __TOL__) {
            out.none.push({ref: desig, caption: c.getState_Name() || '', pin: p.pinNumber,
                name: p.pinName, x: p.x, y: p.y, nc: !!p.noConnected,
                off: nearest === null ? null : nearest.d,
                net: nearest === null ? null : nearest.net});
            continue;
        }
        out.loose.push({ref: desig, caption: c.getState_Name() || '', pin: p.pinNumber,
            name: p.pinName, x: p.x, y: p.y, nc: !!p.noConnected,
            off: nearest.d, net: nearest.net});
    }
}
return out;
"""

PAGES = """
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return pages.map(p => ({uuid: p.uuid, name: p.title || p.name || p.friendlyName || ''}));
"""


def fmt(value, digits=18):
    """Show enough digits that 260.00000000000006 does not read as 260."""
    return f"{value:.{digits}f}".rstrip("0")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=0.01, help="loose ceiling, API units")
    ap.add_argument("--ref", default="", help="restrict the scan to one designator")
    ap.add_argument("--show-none", action="store_true",
                    help="also list tips with no wire within tolerance")
    ap.add_argument("--limit", type=int, default=15,
                    help="rows of the loose table to echo to stdout (0 = none)")
    ap.add_argument("--out", default=str(EVIDENCE))
    args = ap.parse_args()

    pages = execute(PAGES)
    lines, report = [], []
    total = {"scanned": 0, "exact": 0, "none": 0, "fractionalTips": 0}
    for page in pages:
        code = (PAYLOAD.replace("__PAGE__", json.dumps(page["uuid"]))
                .replace("__REF__", json.dumps(args.ref or None))
                .replace("__TOL__", repr(args.tol)))
        r = execute(code)
        r["none"] = r["none"] if isinstance(r["none"], list) else []
        lines.append((page, r))
        total["scanned"] += r["scanned"]
        total["exact"] += r["exact"]
        total["none"] += len(r["none"])
        total["fractionalTips"] += r["fractionalTips"]
        print(f"{page['name']:<28} comps={r['components']:>3} wires={r['wires']:>4} "
              f"tips={r['scanned']:>4} exact={r['exact']:>4} loose={len(r['loose']):>3} "
              f"none={len(r['none']):>4}", file=sys.stderr)

    def label(row):
        return row["ref"] or f"<{row['caption'] or 'port'}>"

    loose = [(page["name"], row) for page, r in lines for row in r["loose"]]
    orphan = [(page["name"], row) for page, r in lines for row in r["none"]]
    worst = max((row["off"] for _, row in loose), default=0)

    text = []
    text.append(f"tolerance: {args.tol!r}   filter: {args.ref or 'all refs'}")
    text.append("")
    text.append(f"{'page':<28} {'comps':>5} {'wires':>6} {'tips':>5} {'exact':>6} "
                f"{'loose':>5} {'none':>5} {'frac-tips':>9}")
    for page, r in lines:
        text.append(f"{page['name']:<28} {r['components']:>5} {r['wires']:>6} "
                    f"{r['scanned']:>5} {r['exact']:>6} {len(r['loose']):>5} "
                    f"{len(r['none']):>5} {r['fractionalTips']:>9}")
    text.append("")
    text.append(f"TOTALS  tips={total['scanned']}  exact={total['exact']}  "
                f"loose={len(loose)}  none={total['none']}  "
                f"fractional pin tips={total['fractionalTips']}")
    text.append(f"largest loose offset = {fmt(worst)}")
    text.append("")

    if loose:
        buckets = {}
        for _, row in loose:
            exponent = 0 if row["off"] == 0 else int(math.floor(math.log10(row["off"])))
            buckets[exponent] = buckets.get(exponent, 0) + 1
        text.append("loose offset magnitudes (orders of magnitude, most-negative first):")
        for exponent in sorted(buckets):
            text.append(f"  1e{exponent:<4} {buckets[exponent]:>5}  "
                        + "#" * min(buckets[exponent], 60))
        text.append("")
        by_part = {}
        for _, row in loose:
            key = label(row)
            hit = by_part.setdefault(key, [0, 0])
            hit[0] += 1
            hit[1] = max(hit[1], row["off"])
        text.append(f"{'part':<16} {'loose tips':>10} {'worst offset':>14}")
        for key, (count, off) in sorted(by_part.items(), key=lambda item: (-item[1][0], item[0])):
            text.append(f"{key:<16} {count:>10} {off:>14.3e}")
        text.append("")

    def table(rows, header):
        out = [header, f"  {'page':<24} {'part':<9} {'pin':<5} {'name':<18} "
                       f"{'tip (x, y)':<28} {'offset':<12} net/nc"]
        for name, row in sorted(rows, key=lambda item: -(item[1]["off"] or float("inf"))):
            tip = f"({fmt(row['x'], 6)}, {fmt(row['y'], 6)})"
            tail = "-" if row["off"] is None else f"{row['off']:<12.3e}"
            extra = row.get("net") or ("NC-flag" if row.get("nc") else "no wire")
            out.append(f"  {name:<24} {label(row):<9} {str(row['pin']):<5} "
                       f"{str(row['name']):<18} {tip:<28} {tail} {extra}")
        return out

    if loose:
        text.extend(table(loose, "loose pin tips (nearest wire endpoint is within "
                                 "tolerance but not on it):"))
    else:
        text.append("loose pin tips: none - no wire endpoint sits within tolerance "
                    "of a pin tip without landing exactly on it.")
    if args.show_none and orphan:
        text.append("")
        text.extend(table(orphan, "tips with NO wire within tolerance (net ports and "
                                  "label-terminated pins belong here; check the rest):"))
    report = "\n".join(text) + "\n"
    Path(args.out).write_text(report)

    head = report.split("\n")
    stop = next(i for i, line in enumerate(head) if line.startswith("loose pin tips"))
    print("\n".join(head[:stop]))
    if args.limit:
        print("  ... first rows:")
        print("\n".join(head[stop:stop + 2 + args.limit]))
    if not args.show_none and orphan:
        print(f"(re-run with --show-none to list the {len(orphan)} tips with no wire "
              f"within tolerance; full detail in {Path(args.out).name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
