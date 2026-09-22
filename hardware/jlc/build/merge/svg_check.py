#!/usr/bin/env python3
"""Audit the client's own SVG export of 10_ALL against the sheet furniture we drew.

The canvas-capture API (`getCurrentRenderedAreaImage`) returns a stale bitmap - three
primitives were added and saved and the PNG came back byte-identical - so the render that
proves "how the sheet reads" is `sch_ManufactureData.getExportDocumentFile(..., 'SVG', ...)`.
SVG is text, so this checks the drawing itself rather than a screenshot of it:

* every border / partition-frame / title-block rectangle is present, with the geometry
  `layout.json` says it should have (SVG x = API x, SVG y = -API y);
* every decoration string (banner, 9 partition titles, their remarks, the title block, the
  legend) actually reaches the page;
* nothing that is NOT furniture is drawn outside the border - the original complaint was
  "content sits outside the drawing frame", and that is now a measurable claim.

    python3 hardware/jlc/build/merge/svg_check.py hardware/jlc/build/merge/preview_10_ALL.svg
"""
import json
import re
import sys
from pathlib import Path

MERGE = Path(__file__).resolve().parent
LAYOUT = MERGE / "layout.json"
BORDER_INK = "808080"
FRAME_INK = "FF9900"
STYLE = re.compile(r'style="([^"]*)"')
PROP = re.compile(r'(stroke|fill|stroke-width):([^;"]+)')
NUM = re.compile(r'(-?[\d.]+)')


def props(style):
    return dict(PROP.findall(style))


def rects(svg):
    out = []
    for m in re.finditer(r'<rect\b[^>]*/?>', svg):
        tag = m.group(0)
        st = STYLE.search(tag)
        if not st:
            continue
        p = props(st.group(1))
        if (p.get("stroke") or "").upper().lstrip("#") not in (BORDER_INK.upper(), FRAME_INK.upper()):
            continue
        g = dict(re.findall(r'\b(x|y|width|height)="(-?[\d.]+)"', tag))
        if len(g) != 4:
            continue
        out.append({
            "ink": p["stroke"].upper().lstrip("#"), "w": float(p.get("stroke-width", 0)),
            # back into API space: +y up, top-left corner
            "box": [float(g["x"]), -float(g["y"]), float(g["width"]), float(g["height"])],
        })
    return out


def texts(svg):
    out = []
    for m in re.finditer(r'<text\b[^>]*>(?:<tspan[^>]*>)?(.*?)(?:</tspan>)?</text>', svg, re.S):
        tag = m.group(0)
        x = re.search(r'\bx="(-?[\d.]+)"', tag)
        y = re.search(r'\by="(-?[\d.]+)"', tag)
        body = re.sub(r'<[^>]+>', '', m.group(1)).replace('&#38;', '&').strip()
        if body:
            out.append({"s": body, "x": float(x.group(1)) if x else None,
                        "y": -float(y.group(1)) if y else None})
    return out


def drawn_extent(svg, border):
    """Bbox of everything the exporter drew that is not the furniture, in API units."""
    x0 = y0 = 1e18
    x1 = y1 = -1e18
    keep = 0
    for m in re.finditer(r'<(polyline|path|circle)\b[^>]*\b(points|d|cx)="([^"]*)"', svg):
        nums = [float(v) for v in NUM.findall(m.group(3))]
        if m.group(1) == "circle":
            nums = nums[:2]
        pts = list(zip(nums[0::2], nums[1::2]))
        if not pts:
            continue
        # `d` carries arc/curve control points; their extremes bound the shape well enough.
        if m.group(2) == "d" and max(abs(v) for _, v in pts) > 1e6:
            continue
        inside = True
        for px, py in pts:
            ax, ay = px, -py
            if abs(ax) > 1e5 or abs(ay) > 1e5:
                inside = False
                break
            if border[0] <= ax <= border[0] + border[2] and border[1] - border[3] <= ay <= border[1]:
                continue
            inside = False
            break
        if inside:
            keep += 1
            continue
        for px, py in pts:
            ax, ay = px, -py
            if abs(ax) > 1e5 or abs(ay) > 1e5:
                continue
            x0, y0 = min(x0, ax), min(y0, ay)
            x1, y1 = max(x1, ax), max(y1, ay)
    return (x0, y0, x1, y1), keep


def main():
    svg = Path(sys.argv[1]).read_text(encoding="utf-8")
    layout = json.loads(LAYOUT.read_text())
    want_frames = {name: cell["frame"] for name, cell in layout["cells"].items()}
    rs = rects(svg)
    frames = [r for r in rs if r["ink"].upper() == FRAME_INK.upper()]
    borders = [r for r in rs if r["ink"].upper() == BORDER_INK.upper()]
    print(f"rectangles: furniture={len(rs)}  frame={len(frames)}  border/title={len(borders)}")

    def close(a, b, tol=1.0):
        return all(abs(x - y) <= tol for x, y in zip(a, b))

    matched = {}
    for name, box in want_frames.items():
        # frame_box() stores [minX, minY, maxX, maxY]; the rect wants top-left + size
        want = [box[0], box[3], box[2] - box[0], box[3] - box[1]]
        hit = next((f for f in frames if close(f["box"], want, 1.5)), None)
        matched[name] = hit
        print(f"  {'OK ' if hit else 'MISS'} frame {name:18s} want={want} got={hit['box'] if hit else None}")
    orphan = [f for f in frames if f not in matched.values()]
    print(f"  unclaimed amber rects: {len(orphan)} (expect 0 - anything here is a probe "
          f"or a duplicated frame)")
    for o in orphan:
        print(f"    {o['box']} w={o['w']}")

    border = min(borders, key=lambda b: -b["box"][2] * b["box"][3])["box"]
    print(f"border rect: topLeft=({border[0]}, {border[1]}) {border[2]}x{border[3]}  ->  API "
          f"x {border[0]}..{border[0] + border[2]},  y {border[1] - border[3]}..{border[1]}")
    ts = texts(svg)
    print(f"text elements in export: {len(ts)}")

    sys.path.insert(0, str(MERGE.parent.parent / "tools"))
    import merge_schematic_pages as M  # noqa: E402  - BLOCK_META is the wording's source of truth
    miss = 0
    for name, (title, notes) in sorted(M.BLOCK_META.items()):
        want = [title] + notes
        got = [w for w in want if any(w == t["s"] for t in ts)]
        miss += len(want) - len(got)
        print(f"  {'OK ' if len(got) == len(want) else 'MISS'} {name:18s} "
              f"title+{len(notes)} notes in export: {len(got)}/{len(want)}")
    fixed = ["AIOT-WATCH · 单页总图 10_ALL", "图例：琥珀色框", "发布闸门 HOLD",
             "本页位号已全部排除出 BOM", "tools/check_sch_netlist_parity.py", "U2 SIM8230C"]
    for probe in fixed:
        hit = [t for t in ts if probe in t["s"]]
        miss += 0 if hit else 1
        print(f"  {'OK ' if hit else 'MISS'} {probe!r} -> {len(hit)}")
    ghost = [t for t in ts if re.search(r"CJK-Abc|PROBE_PAINT|分区备注：", t["s"])]
    print(f"  probe/ghost strings still in the export: {len(ghost)}")
    print(f"decoration wording missing from the render: {miss}")

    # A remark that lands under its own frame's bottom line is the same defect the user
    # complained about, just one level down - so check every decoration string against the
    # frame it belongs to, not just against the page border.
    def width_of(s, size):
        return sum(size if ord(ch) > 0x2E80 else size * 0.55 for ch in s)

    leak = 0
    for name, (title, notes) in sorted(M.BLOCK_META.items()):
        fx0, fy0, fx1, fy1 = layout["cells"][name]["frame"]
        for s, size in [(title, M.TITLE_FS)] + [(n, M.NOTE_FS) for n in notes]:
            hit = next((t for t in ts if t["s"] == s), None)
            if hit is None:
                continue
            # LEFT_TOP anchors grow right and down; the centred title grows both ways.
            left = hit["x"] - (width_of(s, size) / 2 if s == title else 0)
            right = left + width_of(s, size)
            bottom = hit["y"] - size
            ok = fx0 <= left and right <= fx1 and bottom >= fy0 and hit["y"] <= fy1
            if not ok:
                leak += 1
                print(f"  LEAK {name}: {s[:34]!r} spans x {left:.0f}..{right:.0f} "
                      f"y {bottom:.0f}..{hit['y']:.0f} in frame x {fx0:.0f}..{fx1:.0f} "
                      f"y {fy0:.0f}..{fy1:.0f}")
    print(f"decoration strings spilling outside their own partition frame: {leak}")
    miss += leak

    ext, keep = drawn_extent(svg, border)
    if ext[0] == 1e18:
        print(f"content shapes: {keep}, all inside the border")
    else:
        print(f"content shapes: {keep} inside, OUTSIDE bbox x {ext[0]:.0f}..{ext[2]:.0f} "
              f"y {ext[1]:.0f}..{ext[3]:.0f}")
    bad = [t for t in ts if t["x"] is not None and not (
        border[0] <= t["x"] <= border[0] + border[2]
        and border[1] - border[3] - 1 <= t["y"] <= border[1] + 1)]
    print(f"texts outside the border: {len(bad)}")
    for t in bad[:12]:
        print(f"  ({t['x']}, {t['y']}) {t['s'][:60]}")
    return 1 if (miss or bad or ext[0] != 1e18 or ghost) else 0


if __name__ == "__main__":
    sys.exit(main())
