#!/usr/bin/env python3
"""Bounded calculations from kicad-happy topology; constants cite TI documents."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / 'analysis/kicad-happy/schematic.json').read_text())
components = {c['reference']: c for c in data['components']}

def resistance(ref):
    value = components[ref]['value']
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([kM]?)(?: 1%)?', value)
    assert match, (ref, value)
    return float(match[1]) * {'': 1, 'k': 1e3, 'M': 1e6}[match[2]]

def endpoints(net):
    return {(p['component'], str(p['pin_number'])) for p in data['nets'][net]['pins']}

assert endpoints('DCDC_CTRL') == {('U7', '1'), ('U7', '14'), ('R109', '2')}
assert ('R109', '1') in endpoints('SYS')
print(f'R109={resistance("R109"):.0f} ohm; SYS -> R109 -> U7.1 and U7.14; no direct SYS strap remains')
# TPS63070 SLVSC58B p17 section9.2.2.1, VREF=800mV.
voltage = .8 * (1 + resistance('R105') / resistance('R106'))
print(f'VOUT=0.8*(1+{resistance("R105"):.0f}/{resistance("R106"):.0f})={voltage:.6f} V')
# BQ24074 SLUS810N electrical table: nominal KISET=890 Aohm, KILIM=1610 Aohm.
print(f'ICHG=890/{resistance("R101"):.0f}={890/resistance("R101"):.6f} A; ILIM=1610/{resistance("R102"):.0f}={1610/resistance("R102"):.6f} A')
assert endpoints('BAT_NTC') == {('U6', '1')}
print('BAT_NTC endpoints: U6.1 only; no physical NTC or battery connector symbol')
