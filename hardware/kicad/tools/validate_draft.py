#!/usr/bin/env python3
"""Read-only draft checks. This is deliberately not an ERC/DRC replacement."""
from pathlib import Path
import csv
import json
import math
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def parse(path):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', path.read_text())
    stack, result = [], []
    for token in tokens:
        if token == '(':
            node = []
            (stack[-1] if stack else result).append(node)
            stack.append(node)
        elif token == ')':
            assert stack, f'Unexpected closing parenthesis: {path}'
            stack.pop()
        else:
            assert stack, f'Atom outside expression: {path}'
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and len(result) == 1, f'Incomplete expression: {path}'
    return result[0]


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def child(node, key):
    found = children(node, key)
    assert len(found) == 1, (key, len(found))
    return found[0]


def properties(node):
    result = {x[1]: x[2] for x in children(node, 'property')}
    for text in children(node, 'fp_text'):
        if text[1] in ('reference', 'value'):
            result[text[1].capitalize()] = text[2]
    return result


def point(node):
    return tuple(round(float(x), 5) for x in node[1:3])


def main():
    files = sorted(set(ROOT.rglob('*.kicad_sch')) | set(ROOT.rglob('*.kicad_sym')) |
                   set(ROOT.rglob('*.kicad_mod')) | {ROOT / 'pcb/aiot-watch.kicad_pcb',
                   ROOT / 'sym-lib-table', ROOT / 'fp-lib-table'})
    parsed = {p: parse(p) for p in files}
    project = json.loads((ROOT / 'aiot-watch.kicad_pro').read_text())
    assert project['erc']['erc_exclusions'] == []
    for p in (ROOT / 'preview').glob('*.svg'):
        ET.parse(p)
    inventory = json.loads((ROOT / 'docs/design_inventory.json').read_text())
    references = [row['Reference'] for row in inventory['components']]
    assert len(references) == len(set(references)), 'Duplicate BOM references'
    with (ROOT / 'bom/BOM.csv').open() as f:
        bom = list(csv.DictReader(f))
    assert {r['Reference'] for r in bom} == set(references)

    instances, pin_numbers, checked_pins = {}, {}, 0
    for path, tree in parsed.items():
        if path.suffix != '.kicad_sch':
            continue
        for sheet in children(tree, 'sheet'):
            assert (path.parent / properties(sheet)['Sheetfile']).exists(), 'Broken hierarchy'
        libraries = {x[1]: x for x in children(child(tree, 'lib_symbols'), 'symbol')}
        endpoints = set()
        for wire in children(tree, 'wire'):
            for xy in children(child(wire, 'pts'), 'xy'):
                pt = point(xy)
                assert all(abs(v / 1.27 - round(v / 1.27)) < 1e-4 for v in pt), ('Off grid', path, pt)
                endpoints.add(pt)
        labels = {point(child(n, 'at')) for n in children(tree, 'global_label')}
        assert labels <= endpoints, ('Label not on a wire endpoint', path)
        ncs = {point(child(n, 'at')) for n in children(tree, 'no_connect')}
        for symbol in children(tree, 'symbol'):
            ref = properties(symbol)['Reference']
            assert ref not in instances, ('Duplicate schematic reference', ref)
            instances[ref] = symbol
            lib = libraries[child(symbol, 'lib_id')[1]]
            origin = point(child(symbol, 'at'))
            nums = []
            for unit in children(lib, 'symbol'):
                for pin in children(unit, 'pin'):
                    nums.append(child(pin, 'number')[1])
                    at = point(child(pin, 'at'))
                    pos = (round(origin[0] + at[0], 5), round(origin[1] - at[1], 5))
                    assert pos in endpoints or pos in ncs, ('Unintended floating pin', ref, nums[-1], pos)
                    assert not (pos in endpoints and pos in ncs), ('Connected pin marked NC', ref, nums[-1])
                    checked_pins += 1
            assert len(nums) == len(set(nums)), ('Repeated physical pin', ref)
            pin_numbers[ref] = set(nums)
            if ref == 'U1':
                assert set(nums) == {str(i) for i in range(1, 58)}
    for blocked in ['U2', 'U12', 'U13', 'J2', 'J3', 'MIC1']:
        assert blocked not in instances, ('Unverified component acquired pins', blocked)
    # U9/U10 gained pins from published pin tables, so the guard stays as an exact-count check:
    # ES8311 Rev 5.0 lists 20 pins, PAM8302A DS41333 Rev.6-2 lists 8 terminals.
    assert pin_numbers.get('U9') == {str(i) for i in range(1, 21)}, 'ES8311 pin set changed'
    assert pin_numbers.get('U10') == {str(i) for i in range(1, 9)}, 'PAM8302A pin set changed'

    board = parsed[ROOT / 'pcb/aiot-watch.kicad_pcb']
    layers = child(board, 'layers')[1:]
    assert len([x for x in layers if x[1].endswith('.Cu')]) == 6
    assert not children(board, 'segment') and not children(board, 'via')
    lines = children(board, 'gr_line')
    lines = [x for x in lines if child(x, 'layer')[1] == 'Edge.Cuts']
    arcs = children(board, 'gr_arc')
    assert len(lines) == 4 and len(arcs) == 4
    outline_points = [point(child(n, k)) for n in lines + arcs for k in ('start', 'end')]
    assert all(outline_points.count(p) == 2 for p in outline_points), 'Outline is not closed'
    assert math.isclose(max(x for x, y in outline_points) - min(x for x, y in outline_points), 34.5)
    assert math.isclose(max(y for x, y in outline_points) - min(y for x, y in outline_points), 40)
    board_nets = {n[1]: n[2] for n in children(board, 'net')}
    footprints = children(board, 'footprint')
    holes = [f for f in footprints if properties(f)['Reference'].startswith('H')]
    tests = [f for f in footprints if re.fullmatch(r'TP\d+', properties(f)['Reference'])]
    assert len(footprints) == 25 and len(holes) == 4 and len(tests) == 21
    for hole in holes:
        assert child(child(hole, 'pad'), 'drill')[1] == '1.4'
    expected = dict(inventory['testpoints'])
    for tp in tests:
        ref = properties(tp)['Reference']
        net = child(child(tp, 'pad'), 'net')
        assert board_nets[net[1]] == net[2] == expected[ref]
    assert len(children(board, 'zone')) == 16, 'Four annular sectors per mounting hole'
    for zone in children(board, 'zone'):
        child(zone, 'keepout')
        pts = [point(p) for p in children(child(child(zone, 'polygon'), 'pts'), 'xy')]
        center = min((point(child(h, 'at')) for h in holes),
                     key=lambda c: math.dist(c, pts[0]))
        assert all(.749 < math.dist(center, p) <= 1.001 for p in pts), 'Annulus geometry changed'
    for directory in ['gerber', 'drill', 'position', 'bom']:
        assert all(p.suffix == '.md' for p in (ROOT / 'manufacturing' / directory).iterdir())

    cli = shutil.which('kicad-cli')
    report = {
        'status': 'PASS_STATIC_ONLY', 'sexpr_files': len(files),
        'bom_rows': len(bom), 'pin_and_intent_rows': len(inventory['pins']),
        'pin_bearing_symbols': len(instances), 'connected_or_nc_symbol_pins': checked_pins,
        'copper_layers': 6, 'testpads': 21, 'npth_holes': 4,
        'kicad_cli': cli, 'native_checks': 'See NATIVE_CHECK.json; not executed by this script',
        'manufacturing_release': 'BLOCKED',
        'limitations': 'S-expression structure and selected invariants only; not KiCad parsing, ERC, DRC, full connectivity, footprint or electronics verification.'
    }
    if cli:
        report['kicad_version'] = subprocess.run([cli, 'version'], check=True, timeout=30,
                                                capture_output=True, text=True).stdout.strip()
    (ROOT / 'docs/STATIC_CHECK.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
