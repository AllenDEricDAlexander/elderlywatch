#!/usr/bin/env python3
"""Bind real LCSC land patterns onto the devices that KiCad import created.

Import keeps symbols and pins but leaves every footprint empty. This walks the
schematic pages, takes the device each placed part actually references, and
points that device's footprint at the LCSC library entry recorded in
JLC_PART_MAP.csv. The client copies the referenced land pattern into the
project library and stamps `source = <lcscFootprintUuid>|<lcscLibraryUuid>`,
which is what verification reads back - API return values alone are not
believed.

Refs without a resolved LCSC footprint (U1/U10 and everything behind D01-D16)
are reported as skipped, never guessed at.
"""
import argparse
import base64
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eda_run  # noqa: E402

HERE = Path(__file__).resolve().parent
JLC = HERE.parent
BUILD = JLC / "build"
PARTS_CACHE = BUILD / "imported_parts.json"
RESULT = BUILD / "footprint_bind.result.json"
EPRU = BUILD / "aiot-kicad-import.epru"

SCAN = """
const page = __PAGE__;
await eda.dmt_EditorControl.openDocument(page.uuid);
const parts = await eda.sch_PrimitiveComponent.getAll(undefined, false);
return (parts || [])
    .filter(p => p.getState_ComponentType() === 'part')
    .map(p => ({
        page: page.name,
        ref: p.getState_Designator(),
        deviceUuid: (p.getState_Component() || {}).uuid,
        deviceName: (p.getState_Component() || {}).name,
        footprint: (p.getState_Footprint() || {}).uuid,
        mpn: (p.getState_OtherProperty() || {}).MPN,
    }));
"""

PAGES = """
const info = await eda.dmt_Project.getCurrentProjectInfo();
const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
return {project: {uuid: info.uuid, name: info.friendlyName || info.name},
        pages: (pages || []).map(p => ({uuid: p.uuid, name: p.name}))};
"""

BIND = """
const ref = __REF__, lcscId = __LCSC__, expectedFp = __FP__;
const item = (await eda.lib_Device.getByLcscIds([lcscId]))
    .find(d => d.supplierId === lcscId);
if (!item) return {ref, status: 'SKIP', why: lcscId + ' not found in LCSC library'};
if (!item.footprintUuid) return {ref, status: 'SKIP', why: lcscId + ' carries no footprint'};
if (expectedFp && item.footprintUuid !== expectedFp)
    return {ref, status: 'SKIP', why: 'footprint moved: map says ' + expectedFp + ', library says ' + item.footprintUuid};
const ok = await eda.lib_Device.modify(__DEV__, __PLIB__, undefined, undefined,
    {footprintUuid: item.footprintUuid, footprint: {uuid: item.footprintUuid, libraryUuid: item.libraryUuid}});
return {ref, status: ok ? 'BOUND' : 'FAILED', device: __DEV__, lcscId,
        mpn: item.manufacturerId, footprintName: item.footprintName, footprintUuid: item.footprintUuid};
"""

EXPORT = """
const f = await eda.sys_FileManager.getProjectFile('verify.epro2', undefined, 'epro2');
const b = new Uint8Array(await f.arrayBuffer());
let s = '';
for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
return btoa(s);
"""


def export_epru():
    """Pull the project log out of the client and keep it as the evidence file.

    tools/check_footprint_pin_parity.py reads that file, so exporting has to
    refresh it rather than only returning it in memory.
    """
    raw = base64.b64decode(eda_run.execute(EXPORT))
    zf = zipfile.ZipFile(io.BytesIO(raw))
    text = zf.read([n for n in zf.namelist() if n.endswith(".epru")][0]).decode()
    EPRU.write_text(text)
    return text


def read_back(needle=None):
    """Pull device footprint attributes and footprint provenance out of a log.

    `needle` filters device titles; leave it out to read every device, because
    imported devices are not always named `project_*` and a name filter would
    report a real binding as unverified.
    """
    devices, footprints, cur = {}, {}, None
    for line in export_epru().splitlines():
        head, _, body = line.partition("||")
        if not body:
            continue
        try:
            h = json.loads(head)
            b = json.loads(body.rstrip("|"))
        except json.JSONDecodeError:
            continue
        if h["type"] == "DOCHEAD":
            cur = (b["docType"], b["uuid"])
        elif h["type"] == "META" and cur:
            kind, uuid = cur
            if kind == "DEVICE":
                devices[uuid] = {"title": b.get("title"),
                                 "footprint": (b.get("attributes") or {}).get("Footprint")}
            elif kind == "FOOTPRINT":
                footprints[uuid] = {"title": b.get("title"), "source": b.get("source")}
    if needle:
        devices = {u: d for u, d in devices.items() if needle in (d["title"] or "")}
    return devices, footprints


def collect_parts(refresh):
    if PARTS_CACHE.exists() and not refresh:
        return json.loads(PARTS_CACHE.read_text())
    tree = eda_run.execute(PAGES)
    parts = []
    for page in tree["pages"]:
        parts.extend(eda_run.execute(SCAN.replace("__PAGE__", json.dumps(page))))
    cache = {"project": tree["project"], "parts": parts}
    PARTS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    return cache


def targets():
    out = {}
    for row in csv.DictReader(open(JLC / "JLC_PART_MAP.csv")):
        if row["LCSC_ID"].strip() and row["JLC_FOOTPRINT_UUID"].strip():
            out[row["Reference"]] = (row["LCSC_ID"].strip(), row["JLC_FOOTPRINT_UUID"].strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-scan the schematic pages")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--export-only", action="store_true",
                    help="just refresh build/aiot-kicad-import.epru for the parity gate")
    args = ap.parse_args()
    if args.export_only:
        text = export_epru()
        print(f"{EPRU.name}: {len(text.splitlines())} log lines, "
              f"{text.count(chr(34) + 'DOCHEAD')} documents")
        return 0

    cache = collect_parts(args.refresh)
    want = targets()
    devices = {}
    for part in cache["parts"]:
        if part["ref"] in want and part["deviceUuid"]:
            devices.setdefault(part["ref"], set()).add(part["deviceUuid"])

    planned, results = [], []
    for ref, (lcsc, fp) in sorted(want.items()):
        devs = sorted(devices.get(ref, ()))
        if not devs:
            results.append({"ref": ref, "status": "SKIP", "why": "no placed part with this designator"})
        elif len(devs) > 1:
            results.append({"ref": ref, "status": "SKIP", "why": f"{len(devs)} distinct devices on the schematic: {devs}"})
        else:
            planned.append((ref, devs[0], lcsc, fp))

    if args.dry_run:
        print(json.dumps({"project": cache["project"], "planned": [p[0] for p in planned],
                          "results": results}, indent=2, ensure_ascii=False))
        return 0

    project_uuid = cache["project"]["uuid"]
    for ref, dev, lcsc, fp in planned:
        code = (BIND.replace("__REF__", json.dumps(ref)).replace("__LCSC__", json.dumps(lcsc))
                .replace("__FP__", json.dumps(fp)).replace("__DEV__", json.dumps(dev))
                .replace("__PLIB__", json.dumps(project_uuid)))
        try:
            results.append(eda_run.execute(code))
        except Exception as err:  # noqa: BLE001 - report, never swallow silently
            results.append({"ref": ref, "status": "ERROR", "why": str(err)[:200]})
        print(json.dumps(results[-1], ensure_ascii=False))

    # Verify against the saved project log, not against API return values.
    bound = [r for r in results if r.get("status") == "BOUND"]
    devices_read, footprints = read_back()
    local = {u: f for u, f in footprints.items() if f.get("source")}
    for r in bound:
        seen = devices_read.get(r["device"], {})
        r["verifiedFootprint"] = seen.get("footprint")
        src = local.get(seen.get("footprint"), {})
        r["verifiedSource"] = src.get("source")
        r["verifiedName"] = src.get("title")
        r["verified"] = (src.get("source") or "").startswith(r["footprintUuid"])

    summary = {"project": cache["project"], "results": sorted(results, key=lambda r: r["ref"])}
    RESULT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    for state in ("BOUND", "SKIP", "FAILED", "ERROR"):
        rows = [r for r in results if r.get("status") == state]
        if rows:
            print(f"{state}: {', '.join(r['ref'] for r in rows)}")
    print(f"verified on disk: {sum(1 for r in bound if r.get('verified'))}/{len(bound)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
