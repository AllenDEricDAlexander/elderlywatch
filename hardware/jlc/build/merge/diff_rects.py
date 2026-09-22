#!/usr/bin/env python3
"""Why does diff() reject rectangles it just drew? Print both shapes side by side."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import merge_schematic_pages as M  # noqa: E402

names = sorted(M.MAP)
dumps = {n: json.loads((M.MERGE / f"{n}.json").read_text()) for n in names}
cells, total = M.layout(dumps)
expected = []
for name in names:
    cell = cells[name]
    tile = M.items(dumps[name], cell["dx"], cell["dy"])
    for item in tile:
        item["tile"] = name
    expected.extend(tile)
stats = {"refs": 126, "nets": 115, "blocked_part": 12, "blocked_value": 19}
expected.extend(M.decorations(cells, total, stats))

target = {p["name"]: p["uuid"] for p in M.execute(M.PAGES)}[M.TARGET_NAME]
M.execute(M.OPEN.replace("__TARGET__", json.dumps(target)))
live = M.execute(M.VERIFY)
missing, repairs, stray = M.diff(expected, live, 0.05)
want = {M.sig(i): i for i in missing}
print(f"missing={len(missing)} repairs={len(repairs)} stray={len(stray)}")
for kind, rec in stray:
    s = M.shape_of(rec)
    print(f"STRAY {kind:<6} live  = {[repr(v) for v in s]}")
    for sig, item in want.items():
        if sig[0] != kind:
            continue
        e = M.shape_of(item)
        if abs(e[0] - s[0]) < 2 and abs(e[1] - s[1]) < 2:
            print(f"  vs expected {item['label']:<22} {[repr(v) for v in e]}")
            print(f"  deltas: {[round(a - b, 6) for a, b in zip(e, s)]}")
