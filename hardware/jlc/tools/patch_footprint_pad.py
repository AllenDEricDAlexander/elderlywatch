#!/usr/bin/env python3
"""Renumber one pad of a project-library footprint, targeted by position.

Position is part of the key because a single pad number can appear on several
pads (tied/merged leads), and renumbering the wrong one would move a net.

Used for U7: LCSC's VQFN-15 land pattern labels the physical pads that TI's
RNM0015A drawing numbers 8 and 13 as "7" and "12", which leaves the imported
symbol's pins 8/13 with no matching pad.

This is a post-import patch: re-run it after every KiCad re-import.

    python3 hardware/jlc/tools/patch_footprint_pad.py --ref U7 --old 7 --new 8 --x 55.1 --y 37.9
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402
from patch_symbol_pin import device_attrs, IMPORT_RESULT  # noqa: E402

PATCH = """
const fp = __FP__, lib = __LIB__, fromNum = __OLD__, toNum = __NEW__, x = __X__, y = __Y__;
await eda.lib_Footprint.openInEditor(fp, lib);
const src = await eda.sys_FileManager.getDocumentSource();
if (!src) throw new Error('no document source for ' + fp);

function bodyOf(line) {
    const i = line.indexOf('||');
    if (i < 0) return null;
    try {
        return [JSON.parse(line.slice(0, i)), JSON.parse(line.slice(i + 2).replace(/\\|$/, ''))];
    } catch (e) { return null; }
}
const near = (b) => Math.abs(b.centerX - x) < 0.5 && Math.abs(b.centerY - y) < 0.5;
const pads = (s) => (s.split('\\n').map(bodyOf).filter(Boolean)
    .filter(([h, b]) => h.type === 'PAD' && b.num === toNum && near(b)).map(([, b]) => b.num));

if (pads(src).length === 1) return {status: 'ALREADY', pad: toNum, x, y};
const lines = src.split('\\n');
let hits = 0, geometry = null;
for (let i = 0; i < lines.length; i++) {
    const parsed = bodyOf(lines[i]);
    if (!parsed) continue;
    const [head, body] = parsed;
    if (head.type !== 'PAD' || body.num !== fromNum || !near(body)) continue;
    geometry = {num: body.num, centerX: body.centerX, centerY: body.centerY,
        width: (body.defaultPad || {}).width, height: (body.defaultPad || {}).height};
    body.num = toNum;
    lines[i] = lines[i].slice(0, lines[i].indexOf('||')) + '||' + JSON.stringify(body) + '|';
    hits++;
}
if (hits !== 1) throw new Error('pad rewrite count = ' + hits + ' for num ' + fromNum + ' at ' + x + ',' + y);
const ok = await eda.lib_Footprint.updateDocumentSource(fp, lib, lines.join('\\n'));
const after = pads(await eda.sys_FileManager.getDocumentSource());
return {status: (ok && after.length === 1) ? 'PATCHED' : 'FAILED', writeReturned: ok,
    rewrote: geometry, readBack: after};
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--x", required=True, type=float, help="pad centerX, mil")
    ap.add_argument("--y", required=True, type=float, help="pad centerY, mil")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    project_uuid = json.loads(IMPORT_RESULT.read_text())["uuid"]
    device, footprint = device_attrs(args.ref, "Footprint")
    code = (PATCH.replace("__FP__", json.dumps(footprint))
            .replace("__LIB__", json.dumps(project_uuid))
            .replace("__OLD__", json.dumps(args.old))
            .replace("__NEW__", json.dumps(args.new))
            .replace("__X__", json.dumps(args.x))
            .replace("__Y__", json.dumps(args.y)))
    if args.dry_run:
        print(f"ref={args.ref} device={device} footprint={footprint}\n{code}")
        return 0
    print(json.dumps(execute(code), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
