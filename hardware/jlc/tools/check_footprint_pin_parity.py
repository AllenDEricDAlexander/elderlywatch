#!/usr/bin/env python3
"""Compare each bound LCSC land pattern against the symbol pins it must serve.

A footprint that binds cleanly but whose pad numbers do not line up with the
symbol's pin numbers is a silent failure: ERC stays quiet and the mismatch only
surfaces as unroutable nets or a mis-placed part. This reads the project log
straight out of the client's own export, so it checks what was saved rather than
what an API claimed.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent / "build"
LOG = BUILD / "aiot-kicad-import.epru"
BINDINGS = BUILD / "footprint_bind.result.json"

# Pad numbers that legitimately appear on more than one pad, per designator.
# Duplicates are otherwise a defect, so each entry has to name the copper it is.
TIED_PADS = {
    "U7": {
        "7": "TI RNM0015A land pattern: 0.25x0.75mm bar tied to the VOUT pair (pins 7/8)",
        "12": "TI RNM0015A land pattern: 0.25x0.75mm bar tied to the VIN pair (pins 12/13)",
    },
}


def docs(text):
    current, out = None, []
    for line in text.splitlines():
        head, sep, body = line.partition("||")
        if not sep:
            continue
        try:
            h = json.loads(head)
            b = json.loads(body.rstrip("|"))
        except json.JSONDecodeError:
            continue
        if h["type"] == "DOCHEAD":
            current = {"docType": b["docType"], "uuid": b["uuid"], "lines": []}
            out.append(current)
        elif current is not None:
            current["lines"].append((h["type"], h.get("id"), b))
    return {d["uuid"]: d for d in out}


def field(obj, *names, default=None):
    for n in names:
        if n in obj and obj[n] not in (None, ""):
            return obj[n]
    return default


def symbol_pins(doc):
    """Pin numbers a symbol offers.

    The log does not store the number on the PIN record - it hangs off it as a
    separate ATTR whose parentId is the PIN line id, so read the pair together.
    """
    pin_ids = {i for t, i, b in doc["lines"] if t == "PIN"}
    out = [b["value"] for t, i, b in doc["lines"]
           if t == "ATTR" and b.get("key") == "Pin Number" and b.get("parentId") in pin_ids]
    return [str(o) for o in out if o not in (None, "")]


def main():
    if not LOG.exists():
        raise SystemExit(f"{LOG.name} missing - re-export with tools/bind_lcsc_footprints.py")
    index = docs(LOG.read_text())
    symbols = {d["uuid"]: d for d in index.values() if d["docType"] == "SYMBOL"}
    footprints = {d["uuid"]: d for d in index.values() if d["docType"] == "FOOTPRINT"}

    bindings = json.loads(BINDINGS.read_text())["results"]
    rows, problems = [], []
    for row in sorted(bindings, key=lambda r: r["ref"]):
        if row.get("status") != "BOUND":
            rows.append((row["ref"], "-", "-", "-", f"not bound ({row.get('why', 'unknown')})"))
            continue
        device = index.get(row["device"])
        if device is None:
            problems.append(f"{row['ref']}: device {row['device']} absent from the project log")
            continue
        attrs = next((b.get("attributes") or {} for t, i, b in device["lines"] if t == "META"), {})
        sym = symbols.get(attrs.get("Symbol") or "")
        fp = footprints.get(attrs.get("Footprint") or "")
        if sym is None or fp is None:
            problems.append(f"{row['ref']}: unresolved symbol/footprint "
                            f"(Symbol={attrs.get('Symbol')!r} Footprint={attrs.get('Footprint')!r})")
            continue
        pins = symbol_pins(sym)
        pads = [str(field(b, "num", "padNumber", default="")) for t, i, b in fp["lines"] if t == "PAD"]
        unnumbered = sum(1 for p in pads if not p)
        pads = [p for p in pads if p]
        pad_set, pin_set = set(pads), set(pins)
        dup = sorted({p for p in pads if pads.count(p) > 1}, key=lambda s: (len(s), s))
        allowed = TIED_PADS.get(row["ref"], {})
        # a whitelist entry that no longer matches reality is itself a finding
        stale = sorted(n for n in allowed if n not in dup)
        dup = [n for n in dup if n not in allowed]
        missing = sorted(pad_set - pin_set, key=lambda s: (len(s), s))
        unlanded = sorted(pin_set - pad_set, key=lambda s: (len(s), s))
        provenance = (next((b.get("source") for t, i, b in fp["lines"] if t == "META"), "") or "")
        fp_name = next((b.get("title") for t, i, b in fp["lines"] if t == "META"), "?")
        if stale:
            problems.append(f"{row['ref']} [{fp_name}]: TIED_PADS entry no longer duplicated: {stale}")
        note = "dup:" + ",".join(dup) if dup else ("no-LCSC-source" if not provenance else "ok")
        if not dup and allowed:
            note = "tied-pads ok"
        if unnumbered:
            note += f"+{unnumbered}unnum"
        rows.append((row["ref"], fp_name, f"{len(pins)} pins/{len(pad_set)} pads",
                     f"{len(unlanded)} missing / {len(missing)} extra", note))
        if unlanded or missing or dup or not provenance:
            problems.append(f"{row['ref']} [{fp_name}]: "
                            f"pins without pad={unlanded or '-'} pads without pin={missing or '-'} "
                            f"duplicate pad numbers={dup or '-'} footprint source={provenance or 'MISSING'}")

    print(f"{'ref':<5} {'footprint':<40} {'geometry':<16} {'delta':<18} note")
    for r in rows:
        print(f"{r[0]:<5} {str(r[1])[:40]:<40} {str(r[2]):<16} {str(r[3]):<18} {r[4]}")
    print(f"\n{len(problems)} mismatch(es):")
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
