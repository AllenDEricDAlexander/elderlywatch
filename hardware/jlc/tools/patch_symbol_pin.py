#!/usr/bin/env python3
"""Renumber one pin of a project-library symbol through the live client.

Used to align our imported KiCad symbols with the pad numbering of the LCSC
land patterns bound onto them (exposed pads: KiCad says "EP", the datasheet /
LCSC pattern says 9, 17, ...). Pin *names* stay untouched, so the symbol still
reads as EP/THERMAL_PAD - only the number used for pin-to-pad matching moves.

This is a post-import patch: re-run it after every KiCad re-import.

    python3 hardware/jlc/tools/patch_symbol_pin.py --ref U5 --old EP --new 9 --name EP
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402

BUILD = HERE.parent / "build"
IMPORT_RESULT = BUILD / "import_kicad.result.json"

PATCH = """
const sym = __SYM__, lib = __LIB__, fromNum = __OLD__, toNum = __NEW__, name = __NAME__;
await eda.lib_Symbol.openInEditor(sym, lib);
const src = await eda.sys_FileManager.getDocumentSource();
if (!src) throw new Error('no document source for ' + sym);

function parse(src) {
    const out = [];
    for (const line of src.split('\\n')) {
        const i = line.indexOf('||');
        if (i < 0) continue;
        out.push([line.slice(0, i), JSON.parse(line.slice(i + 2).replace(/\\|$/, ''))]);
    }
    return out;
}

const records = parse(src);
const pinIds = new Set(records.filter(([h]) => JSON.parse(h).type === 'PIN').map(([h]) => JSON.parse(h).id));
const byParent = {};
for (const [h, b] of records) {
    if (JSON.parse(h).type === 'ATTR' && pinIds.has(b.parentId)) (byParent[b.parentId] = byParent[b.parentId] || {})[b.key] = b;
}
let target = null, targetParent = null, siblings = [];
for (const [parentId, attrs] of Object.entries(byParent)) {
    const num = attrs['Pin Number'], nm = attrs['Pin Name'];
    if (!num || num.value !== fromNum) continue;
    if (name && nm && nm.value !== name) { siblings.push(nm.value); continue; }
    target = num; targetParent = parentId;
}
if (!target) {
    const done = Object.values(byParent).some(a => a['Pin Number'] && a['Pin Number'].value === toNum &&
        (!name || (a['Pin Name'] && a['Pin Name'].value === name)));
    if (done) return {status: 'ALREADY', pin: toNum, name: name || null};
    throw new Error('no pin numbered ' + fromNum + (name ? ' named ' + name : '') +
        (siblings.length ? ' (found names: ' + siblings.join(',') + ')' : ''));
}
if (target.value === toNum) return {status: 'ALREADY', pin: fromNum, name: name || null};
const isTarget = (b) => b.key === 'Pin Number' && b.parentId === targetParent;
const lines = src.split('\\n');
let hits = 0;
for (let i = 0; i < lines.length; i++) {
    const j = lines[i].indexOf('||');
    if (j < 0) continue;
    let head, body;
    try {
        head = JSON.parse(lines[i].slice(0, j));
        body = JSON.parse(lines[i].slice(j + 2).replace(/\\|$/, ''));
    } catch (e) { continue; }
    if (head.type !== 'ATTR' || !isTarget(body)) continue;
    body.value = toNum;
    lines[i] = lines[i].slice(0, j) + '||' + JSON.stringify(body) + '|';
    hits++;
}
if (hits !== 1) throw new Error('target ATTR line rewrite count = ' + hits);
const ok = await eda.lib_Symbol.updateDocumentSource(sym, lib, lines.join('\\n'));
const after = parse(await eda.sys_FileManager.getDocumentSource())
    .filter(([h, b]) => JSON.parse(h).type === 'ATTR' && isTarget(b))
    .map(([, b]) => b.value);
return {status: (ok && after.length === 1 && after[0] === toNum) ? 'PATCHED' : 'FAILED',
    writeReturned: ok, readBack: after, pinName: byParent[targetParent]['Pin Name']?.value};
"""


def device_attrs(ref, key="Symbol"):
    """Resolve a designator to (device uuid, associated library document uuid).

    Reads the exported project log rather than an API so the answer is what is
    actually on disk. The uuids are stable across edits, so a stale export is
    still a valid lookup.
    """
    log = BUILD / "aiot-kicad-import.epru"
    if not log.exists():
        raise SystemExit(f"{log.name} missing - re-export first (tools/bind_lcsc_footprints.py)")
    device_uuid, attrs = None, {}
    current = None
    for line in log.read_text().splitlines():
        head, sep, body = line.partition("||")
        if not sep:
            continue
        try:
            h, b = json.loads(head), json.loads(body.rstrip("|"))
        except json.JSONDecodeError:
            continue
        if h["type"] == "DOCHEAD":
            current = b
        elif h["type"] == "META" and current and current["docType"] == "DEVICE":
            name = b.get("title") or ""
            if name == f"project_{ref}" or name.startswith(f"project_{ref}_"):
                device_uuid, attrs = current["uuid"], b.get("attributes") or {}
    if not device_uuid:
        raise SystemExit(f"device project_{ref} not found in {log.name}")
    if not attrs.get(key):
        raise SystemExit(f"device {device_uuid} ({ref}) has no {key} attribute")
    return device_uuid, attrs[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--name", default="", help="guard: the pin name that must sit on this number")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    project_uuid = json.loads(IMPORT_RESULT.read_text())["uuid"]
    device, symbol = device_attrs(args.ref)
    code = (PATCH.replace("__SYM__", json.dumps(symbol))
            .replace("__LIB__", json.dumps(project_uuid))
            .replace("__OLD__", json.dumps(args.old))
            .replace("__NEW__", json.dumps(args.new))
            .replace("__NAME__", json.dumps(args.name)))
    if args.dry_run:
        print(f"ref={args.ref} device={device} symbol={symbol}\n{code}")
        return 0
    print(json.dumps(execute(code), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
