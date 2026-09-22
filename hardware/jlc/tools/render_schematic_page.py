#!/usr/bin/env python3
"""Save the real render of a schematic page - straight out of the client's own exporter.

    python3 hardware/jlc/tools/render_schematic_page.py                     # 10_ALL as SVG
    python3 hardware/jlc/tools/render_schematic_page.py --format PNG
    python3 hardware/jlc/tools/render_schematic_page.py --page 01_POWER --out /tmp/power.svg

DO NOT use `dmt_EditorControl.getCurrentRenderedAreaImage()` for evidence. It looks like a
screenshot API and is not: three primitives were created and saved on 10_ALL and the returned
PNG came back byte-identical (same md5), and it did not change when `zoomToRegion()` was
called, because `openDocument()` only accepts the BARE page uuid - hand it `uuid@project` and
it returns `undefined`, so every zoom and grab then silently lands on whichever canvas last
had focus. The exporter is honest instead: `sch_ManufactureData.getExportDocumentFile()`
re-renders from the document, and it is text (SVG) so `build/merge/svg_check.py` can assert
geometry on it rather than eyeball a thumbnail.

It is also the more demanding witness: 10_ALL's export carried 38 `备注CJK-Abc` probe texts
that `sch_PrimitiveText.getAll()` no longer lists and that `delete()` refuses to touch
(`get()` -> null, `delete()` -> false). If the API can see it, the export can see it; the
converse is exactly the rot that forces a rebuild into a fresh page.
"""
import argparse
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eda_run import execute  # noqa: E402

MERGE = HERE.parent / "build" / "merge"
PAGES = """
return (await eda.dmt_Schematic.getAllSchematicPagesInfo())
    .map(p => ({uuid: p.uuid, name: p.title || p.name || ''}));
"""
EXPORT = """
const tab = await eda.dmt_EditorControl.openDocument(__PAGE__);
if (!tab) throw new Error('openDocument() returned nothing for ' + __PAGE__);
await eda.dmt_EditorControl.activateDocument(tab);
const f = await eda.sch_ManufactureData.getExportDocumentFile(__NAME__, __TYPE__,
    {theme: 'Black on White', lineWidth: 'Default'}, 'Current Schematic Page');
if (!f) throw new Error('getExportDocumentFile() returned no file');
const buf = new Uint8Array(await f.arrayBuffer());
let s = '';
const STEP = 8192;
for (let i = 0; i < buf.length; i += STEP) {
    s += String.fromCharCode.apply(null, buf.subarray(i, i + STEP));
}
return {name: f.name, bytes: buf.length, tab: tab, b64: btoa(s)};
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="10_ALL")
    ap.add_argument("--format", default="SVG", choices=["SVG", "PNG", "PDF"])
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    pages = {p["name"]: p["uuid"] for p in execute(PAGES)}
    if args.page not in pages:
        raise SystemExit(f"no page named {args.page} - have: {', '.join(sorted(pages))}")
    name = f"{args.page}.{args.format.lower()}"
    shot = execute(EXPORT.replace("__PAGE__", json.dumps(pages[args.page]))
                   .replace("__NAME__", json.dumps(name))
                   .replace("__TYPE__", json.dumps(args.format)))
    out = Path(args.out or (MERGE / f"preview_{args.page}.{args.format.lower()}"))
    out.write_bytes(base64.b64decode(shot["b64"]))
    print(f"{out}  {args.format}  {shot['bytes']} bytes  as={shot['name']}  tab={shot['tab']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
