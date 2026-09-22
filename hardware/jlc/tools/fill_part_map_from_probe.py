#!/usr/bin/env python3
"""Fill the LCSC columns of JLC_PART_MAP.csv from a live library probe.

Input is the JSON reply of tools/eda_run.py on build/lcsc_probe.js, i.e. real
`lib_Device.search()` output from the running 嘉立创EDA client. Nothing is
invented: a row is only filled when the vendor part number matches on its own.

    python3 hardware/jlc/tools/fill_part_map_from_probe.py \
        hardware/jlc/build/lcsc_probe.result.json
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JLC = HERE.parent
PART_MAP = JLC / "JLC_PART_MAP.csv"

FILL = {
    "LCSC_ID": "supplierId",
    "JLC_DEVICE_UUID": "uuid",
    "JLC_SYMBOL": "symbolName",
    "JLC_SYMBOL_UUID": "symbolUuid",
    "JLC_FOOTPRINT": "footprintName",
    "JLC_FOOTPRINT_UUID": "footprintUuid",
}


def decide(candidates, mpn):
    """Return (candidate or None, decision note)."""
    exact = [c for c in candidates if c.get("manufacturerId") == mpn]
    if len(exact) == 1:
        return exact[0], f"精确命中 {mpn}；唯一候选，待封装二次核对（D07）"
    if len(exact) > 1:
        opts = "; ".join(f"{c.get('supplierId')}={c.get('name')}" for c in exact)
        return None, f"多个精确命中，需选型：{opts}"
    reel = [c for c in candidates if str(c.get("manufacturerId", "")).startswith(mpn)]
    if len(reel) == 1:
        return reel[0], (
            f"库内料号为 {reel[0].get('manufacturerId')}（{mpn} 的包装后缀），"
            "按卷带料号采用"
        )
    opts = "; ".join(
        f"{c.get('supplierId')}={c.get('manufacturerId')}/{c.get('footprintName')}"
        for c in candidates
    )
    return None, f"无精确命中，需选型：{opts}"


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    probe = json.load(open(argv[0]))
    result = probe.get("result", probe)
    by_ref = {f["ref"]: f["candidates"] for f in result["found"]}

    rows = list(csv.DictReader(open(PART_MAP)))
    fields = list(rows[0].keys())
    filled, held = [], []
    for row in rows:
        candidates = by_ref.get(row["Reference"])
        if not candidates:
            continue
        if row["Tier"] != "IC_LCSC_BY_MPN":
            raise SystemExit(f"{row['Reference']} in probe but tier={row['Tier']}")
        match, note = decide(candidates, row["MPN"])
        row["DECISION"] = note
        if match:
            for col, key in FILL.items():
                row[col] = match.get(key, "")
            filled.append(row["Reference"])
        else:
            held.append(row["Reference"])

    with open(PART_MAP, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{PART_MAP.name}: filled {len(filled)} -> {', '.join(sorted(filled))}")
    print(f"                 held   {len(held)} -> {', '.join(sorted(held))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
