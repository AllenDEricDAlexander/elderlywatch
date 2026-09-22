#!/usr/bin/env python3
"""Import ../kicad/ into 嘉立创EDA专业版 as a new project through the bridge.

Zips the KiCad sources, embeds them as base64 into a payload, and hands the
payload to eda_run.py so the client's own KiCad importer builds the project.
The client's createBoard()/createSchematic() write path leaves the document
tree unreadable (see README), so import is the only bootstrap that works.
"""
import argparse
import base64
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
JLC = HERE.parent
KICAD = JLC.parent / "kicad"

INCLUDE = [
    "aiot-watch.kicad_pro",
    "aiot-watch.kicad_sch",
    "aiot-watch.kicad_pcb",
    "fp-lib-table",
    "sym-lib-table",
    "schematic",
    "symbols",
    "footprints",
]

PAYLOAD = """const teams = await eda.dmt_Team.getAllTeamsInfo();
const teamUuid = (teams && teams[0] && teams[0].uuid) || null;
const bin = atob("__B64__");
const bytes = new Uint8Array(bin.length);
for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
const file = new File([bytes], "__ZIPNAME__", {type: 'application/zip'});
const p = await eda.sys_FileManager.importProjectByProjectFile(file, 'KiCad', undefined, {operation: 'New Project', newProjectOwnerTeamUuid: teamUuid, newProjectFriendlyName: "__PROJECT_NAME__"});
return {teamUuid, imported: p ? {uuid: p.uuid, name: p.friendlyName || p.name} : String(p)};
"""


def build_zip() -> bytes:
    buf = io.BytesIO()
    missing = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in INCLUDE:
            src = KICAD / name
            if not src.exists():
                missing.append(name)
                continue
            if src.is_dir():
                for f in sorted(src.rglob("*")):
                    if f.is_file() and f.suffix in (".kicad_sch", ".kicad_sym", ".kicad_mod", "-table"):
                        zf.write(f, f.relative_to(KICAD))
            else:
                zf.write(src, name)
    if missing:
        raise SystemExit(f"missing KiCad input(s): {', '.join(missing)}")
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-name", default="aiot-watch-jlc")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = build_zip()
    code = (PAYLOAD
            .replace("__B64__", base64.b64encode(data).decode())
            .replace("__ZIPNAME__", f"{args.project_name}.zip")
            .replace("__PROJECT_NAME__", args.project_name))
    out = JLC / "build" / "import_kicad.js"
    out.write_text(code)
    print(f"{out.name}: {len(data)} byte zip -> {len(code)} byte payload; project={args.project_name}")
    if args.dry_run:
        # payloads are top-level-await bodies for the bridge, not valid CJS files:
        # syntax-check them wrapped in an async function.
        wrapper = JLC / "build" / "import_kicad.check.mjs"
        wrapper.write_text(f"async function __check(eda) {{\n{code}\n}}\n")
        subprocess.run(["node", "--check", str(wrapper)], check=True)
        wrapper.unlink()
        print(f"node --check OK; re-import target project name: {args.project_name}")
        return 0

    proc = subprocess.run(
        [sys.executable, str(HERE / "eda_run.py"), str(out)],
        capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode:
        return proc.returncode
    imported = json.loads(proc.stdout).get("imported") or {}
    if imported.get("uuid"):
        (JLC / "build" / "import_kicad.result.json").write_text(json.dumps(
            {"projectName": args.project_name, **imported}, indent=2, ensure_ascii=False))
        print(f"\nproject uuid: {imported['uuid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
