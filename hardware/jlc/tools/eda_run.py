#!/usr/bin/env python3
"""POST a build payload to the EasyEDA Pro bridge and print the JSON reply.

Usage:
    python3 hardware/jlc/tools/eda_run.py hardware/jlc/build/lcsc_probe.js
    python3 hardware/jlc/tools/eda_run.py --dry-run <payload.js>

Placeholders substituted from JLC_PART_MAP.csv before sending:
    __PARTS__   [{ref, mpn, lcscId}, ...] for every IC_LCSC_BY_MPN row
"""
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PART_MAP = HERE.parent / "JLC_PART_MAP.csv"
PORTS = range(49620, 49630)


def find_bridge():
    for port in PORTS:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as r:
                body = json.loads(r.read())
        except (urllib.error.URLError, ValueError, TimeoutError):
            continue
        if body.get("service") == "easyeda-bridge":
            return port, body
    raise SystemExit("bridge not running: node ~/.qoder-cn/skills/easyeda-api-skill/scripts/bridge-server.mjs")


def parts():
    path = PART_MAP
    if not path.exists():
        raise SystemExit(f"{path} missing - run tools/gen_jlc_part_map.py first")
    out = []
    for row in csv.DictReader(open(path)):
        if row["Tier"] != "IC_LCSC_BY_MPN":
            continue
        out.append({
            "ref": row["Reference"],
            "mpn": row["MPN"],
            "lcscId": row["LCSC_ID"].strip(),
        })
    return out


def execute(code):
    """Send one payload and return the decoded result.

    One request per call: the bridge itself gives up after 30s, so callers
    chunk multi-document work instead of chaining it into one big payload.
    """
    port, health = find_bridge()
    if not health.get("edaConnected"):
        raise SystemExit(
            f"bridge on :{port} is up but no EasyEDA window is connected "
            f"(edaWindowCount={health.get('edaWindowCount')}). "
            "Install run-api-gateway.eext in 嘉立创EDA专业版 and enable external interaction."
        )
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/execute",
        data=json.dumps({"code": code}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            reply = json.loads(r.read())
    except urllib.error.HTTPError as err:
        # the bridge answers 500 with the client-side exception in the body
        raise RuntimeError(f"HTTP {err.code}: {err.read().decode(errors='replace')}") from None
    if not reply.get("success"):
        raise RuntimeError(reply.get("error") or json.dumps(reply, ensure_ascii=False))
    return reply.get("result")


def main(argv):
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    code = Path(args[0]).read_text().replace("__PARTS__", json.dumps(parts()))
    if dry:
        print(code)
        return 0
    print(json.dumps(execute(code), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
