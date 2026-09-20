#!/usr/bin/env python3
"""Run native checks without launching a GUI or exporting manufacturing data.

Exit 5 means genuine ERC/DRC/parity findings remain. No rule is suppressed.
The saved input hashes identify exactly which editable files were checked.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    cli = shutil.which('kicad-cli')
    if not cli:
        raise SystemExit('kicad-cli not found')
    logs = ROOT / 'docs/checks/latest'
    logs.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(label, args, allowed=(0,)):
        command = [cli] + args
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        (logs / (label + '.log')).write_text(result.stdout + result.stderr)
        commands.append({'command': command, 'exit_code': result.returncode,
                         'log': str((logs / (label + '.log')).relative_to(ROOT))})
        if result.returncode not in allowed:
            raise RuntimeError(f'{label} failed ({result.returncode}); see {logs / (label + ".log")}')
        return result.stdout.strip()

    version = run('version', ['version'])
    # Use the project-root board entry so --schematic-parity finds the full hierarchy.
    assert (ROOT / 'aiot-watch.kicad_pcb').samefile(ROOT / 'pcb/aiot-watch.kicad_pcb')
    run('erc', ['sch', 'erc', '--format', 'json', '--units', 'mm', '--severity-all',
                '--exit-code-violations', '-o', 'docs/erc.json', 'aiot-watch.kicad_sch'], (0, 5))
    run('drc', ['pcb', 'drc', '--format', 'json', '--units', 'mm', '--severity-all',
                '--schematic-parity', '--exit-code-violations', '-o', 'docs/drc.json',
                'aiot-watch.kicad_pcb'], (0, 5))
    run('netlist', ['sch', 'export', 'netlist', '--format', 'kicadxml', '-o',
                    'docs/aiot-watch.net.xml', 'aiot-watch.kicad_sch'])

    inventory = json.loads((ROOT / 'docs/design_inventory.json').read_text())
    netlist = ET.parse(ROOT / 'docs/aiot-watch.net.xml').getroot()
    actual = {}
    for net in netlist.findall('./nets/net'):
        for node in net.findall('node'):
            key = (node.get('ref'), node.get('pin'))
            assert key not in actual, ('Pin on multiple native nets', key)
            actual[key] = net.get('name')
    checked = 0
    for row in inventory['pins']:
        if row['Pin'] == 'TBD' or row['Net'] in ('TBD', 'NC'):
            continue
        key = (row['Reference'], row['Pin'])
        assert actual.get(key) == row['Net'], ('Native net differs from design', key, actual.get(key), row['Net'])
        checked += 1
    expected_refs = {r['Reference'] for r in inventory['pins'] if r['Pin'] != 'TBD'}
    assert expected_refs == {c.get('ref') for c in netlist.findall('./components/comp')}

    # Keep stable preview filenames; SVGs now come from KiCad, not a custom renderer.
    with tempfile.TemporaryDirectory(prefix='aiot-kicad-svg-') as output:
        run('schematic-svg', ['sch', 'export', 'svg', '-o', output + '/', 'aiot-watch.kicad_sch'])
        rendered = list(Path(output).glob('*.svg'))
        assert len(rendered) == 10, ('Missing hierarchy pages', len(rendered))
        for path in rendered:
            if path.stem == 'aiot-watch':
                name = 'PROJECT_ENTRY.svg'
            elif path.stem == 'aiot-watch-00_TOP':
                name = '00_TOP.svg'
            else:
                name = path.stem.removeprefix('aiot-watch-00_TOP-') + '.svg'
            shutil.copyfile(path, ROOT / 'preview' / name)
    for side, layers in [('TOP', 'F.Cu,F.Silkscreen,User.Drawings,Edge.Cuts'),
                         ('BOTTOM', 'B.Cu,B.Fab,B.Silkscreen,User.Comments,Edge.Cuts')]:
        run('pcb-' + side.lower(), ['pcb', 'export', 'svg', '--mode-single', '--fit-page-to-board',
                                   '--exclude-drawing-sheet', '--layers', layers,
                                   *(['--mirror'] if side == 'BOTTOM' else []),
                                   '-o', f'preview/PCB_{side}.svg', 'aiot-watch.kicad_pcb'])

    erc = json.loads((ROOT / 'docs/erc.json').read_text())
    drc = json.loads((ROOT / 'docs/drc.json').read_text())
    erc_items = [v for s in erc['sheets'] for v in s['violations']]

    def summarize(items):
        return {'total': len(items), 'by_severity': dict(Counter(v['severity'] for v in items)),
                'by_type': dict(Counter(v['type'] for v in items))}

    paths = sorted({*ROOT.rglob('*.kicad_sch'), *ROOT.rglob('*.kicad_sym'),
                    *ROOT.rglob('*.kicad_mod'), ROOT / 'aiot-watch.kicad_pro',
                    ROOT / 'pcb/aiot-watch.kicad_pcb', ROOT / 'sym-lib-table', ROOT / 'fp-lib-table'})
    report = {'kicad_version': version, 'native_load': 'PASS',
              'native_netlist': {'components': len(expected_refs), 'checked_pin_net_assignments': checked,
                                 'matches_declared_connected_pins': True},
              'erc': summarize(erc_items), 'drc': summarize(drc['violations']),
              'unconnected_items': summarize(drc['unconnected_items']),
              'schematic_parity': summarize(drc['schematic_parity']),
              'manufacturing_release': 'BLOCKED',
              'limitations': 'Most component footprints and several circuits are absent; zero geometric DRC does not establish a usable board.',
              'inputs_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'commands': commands}
    (ROOT / 'docs/NATIVE_CHECK.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('commands', 'inputs_sha256')},
                     ensure_ascii=False, indent=2))
    return 5 if erc_items or drc['violations'] or drc['unconnected_items'] or drc['schematic_parity'] else 0


if __name__ == '__main__':
    sys.exit(main())
