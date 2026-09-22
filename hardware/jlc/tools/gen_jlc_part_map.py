#!/usr/bin/env python3
"""Generate hardware/jlc/JLC_PART_MAP.csv from the authoritative KiCad BOM.

The JLC tree is an implementation of hardware/kicad, so the device list is read
from ../kicad/bom/BOM.csv rather than maintained twice. Columns an operator
fills in while browsing the LCSC library (LCSC_ID / JLC_SYMBOL / JLC_FOOTPRINT /
DECISION) are carried over across regenerations, keyed by Reference.
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
JLC = HERE.parent
KICAD = JLC.parent / "kicad"
BOM = KICAD / "bom" / "BOM.csv"
INVENTORY = KICAD / "docs" / "design_inventory.json"
OUT = JLC / "JLC_PART_MAP.csv"

# Filled in by a human (or by tools/fill_part_map_from_probe.py) against the
# LCSC library; never invented here.
OPERATOR_COLUMNS = [
    "LCSC_ID", "JLC_DEVICE_UUID", "JLC_SYMBOL", "JLC_SYMBOL_UUID",
    "JLC_FOOTPRINT", "JLC_FOOTPRINT_UUID", "DECISION",
]

IC_REFS_VERIFIED = {
    "U1", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U10", "U11",
}

# D-numbers: hardware/kicad/docs/TODO_DATASHEET_VERIFY.md
BLOCKERS = {
    "U2": "D01", "J2": "D03", "D2": "D03", "U12": "D12",
    "J3": "D02", "U13": "D02",
    "MIC1": "D05",
    "J5": "D09", "NTC1": "D09", "J4": "D11", "J6": "D11", "J1": "D11",
    "SW1": "D11", "SW2": "D11", "ESIM1": "D11",
    "D1": "D13", "D3": "D13", "D4": "D13", "D5": "D13",
    "L101": "D13", "FB1": "D13",
}
RF_BLOCKED = ["ANT1", "ANT2", "ANT3", "ANT4", "C301", "C302", "C303", "C304",
              "C305", "C306", "C307", "C308", "R301", "R302", "R303", "R304"]

BIG_CAP_UF = re.compile(r"(\d+(?:\.\d+)?)u", re.I)


def proposed_package(row):
    """Return (package, note) without pretending a decision was made."""
    ref, cat, value = row["Reference"], row["Category"], row["Value"]
    if cat == "IC":
        return (row["Package"], "land pattern 需按 D07 二次审核后建库") if ref in IC_REFS_VERIFIED \
            else ("待定", "无核实引脚，禁止建库")
    if cat == "Test point":
        return ("PCB 焊盘", "非采购件：嘉立创侧画成 1.0mm 铜盘 + 网络标签")
    if ref in RF_BLOCKED:
        return ("待定", "RF 匹配/天线未定，D10/D13")
    if cat == "Resistor":
        return ("0402 (建议)", "D13：最终封装与耐压/公差待确认")
    if cat == "Capacitor":
        m = BIG_CAP_UF.search(value)
        uf = float(m.group(1)) if m else 0.0
        if "low ESR" in value.lower() or uf >= 100:
            return ("待定", "大容量/低 ESR，0402 不可行，D13")
        if uf >= 10:
            return ("0603 或 0805 (建议)", "10u/22u 在 0402 内容量偏紧，D13")
        return ("0402 (建议)", "D13：最终封装待确认")
    return ("待定", "非通用件，D13")


def classify(row):
    ref, cat = row["Reference"], row["Category"]
    if cat == "Test point":
        return "PCB_FEATURE", ""
    if ref in IC_REFS_VERIFIED:
        return "IC_LCSC_BY_MPN", ""
    if "TBD" in row["Value"].upper():
        return "BLOCKED_VALUE", BLOCKERS.get(ref, "D13")
    if cat in ("Resistor", "Capacitor", "Inductor", "Ferrite bead", "Thermistor"):
        return "PASSIVE_BY_VALUE", "" if cat in ("Resistor", "Capacitor") else BLOCKERS.get(ref, "D13")
    return "BLOCKED_PART", BLOCKERS.get(ref, "D13")


def lcsc_key(row, tier, pkg):
    if tier == "IC_LCSC_BY_MPN":
        return row["MPN"]
    if tier == "PASSIVE_BY_VALUE":
        if "待定" in pkg:
            return ""
        size = pkg.replace("(建议)", "").strip()
        return f'{row["Value"].split("/")[0].strip()} {size}'
    return ""


def main():
    bom_rows = list(csv.DictReader(open(BOM)))
    # design_inventory "pins" mixes real numbered pins with net-intent rows whose
    # Pin field is literally TBD; only numbered pins count as verified.
    pins = json.load(open(INVENTORY))["pins"]
    pin_count = {}
    for p in pins:
        if p["Pin"] not in ("TBD", "", None):
            pin_count[p["Reference"]] = pin_count.get(p["Reference"], 0) + 1

    previous = {}
    if OUT.exists():
        for r in csv.DictReader(open(OUT)):
            previous[r["Reference"]] = r

    header = [
        "Reference", "Qty", "Category", "Value", "Manufacturer", "MPN",
        "Verified_Pins", "Tier", "Proposed_Package", "LCSC_Search_Key",
        "Blocker_Or_Note",
    ] + OPERATOR_COLUMNS
    written = 0
    with open(OUT, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in sorted(bom_rows, key=lambda r: (r["Category"], r["Reference"])):
            tier, blocker = classify(row)
            pkg, note = proposed_package(row)
            old = previous.get(row["Reference"], {})
            operator = [old.get(c, "") for c in OPERATOR_COLUMNS]
            writer.writerow([
                row["Reference"], row["Quantity"], row["Category"], row["Value"],
                row["Manufacturer"], row["MPN"], pin_count.get(row["Reference"], 0),
                tier, pkg, lcsc_key(row, tier, pkg), blocker or note,
            ] + operator)
            written += 1

    from collections import Counter
    tiers = Counter(classify(r)[0] for r in bom_rows)
    print(f"{OUT.name}: {written} rows")
    for tier, count in sorted(tiers.items()):
        print(f"  {tier:<18} {count}")


if __name__ == "__main__":
    main()
