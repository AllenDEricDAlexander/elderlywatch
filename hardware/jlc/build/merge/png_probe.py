#!/usr/bin/env python3
"""Decode a PNG with stdlib only and report where given colours actually landed.

The render is the only evidence about how the merged sheet READS, and at 1794x1118 the eye
cannot tell "not painted" from "painted in a hairline". So ask the pixels instead:

    python3 hardware/jlc/build/merge/png_probe.py preview_all.png FF9900 808080 0066FF
"""
import struct
import sys
import zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, header = 8, b"", None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + length
    width, height, depth, color, *_ = header
    assert depth == 8 and color in (2, 6), f"unsupported depth={depth} color={color}"
    bpp = 3 if color == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * bpp
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(height):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b, c = prev[x], prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        rows.append(bytes(line))
        prev = line
    return width, height, bpp, rows


def main():
    path = sys.argv[1]
    targets = [(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) for h in sys.argv[2:]]
    tol = 40
    width, height, bpp, rows = read_png(path)
    print(f"{path}: {width}x{height}")
    for tr, tg, tb in targets:
        n = 0
        box = None
        for y, row in enumerate(rows):
            for x in range(0, width * bpp, bpp):
                if (abs(row[x] - tr) <= tol and abs(row[x + 1] - tg) <= tol
                        and abs(row[x + 2] - tb) <= tol):
                    n += 1
                    px = x // bpp
                    box = (px, y, px, y) if box is None else (min(box[0], px), min(box[1], y),
                                                              max(box[2], px), max(box[3], y))
        print(f"  #{tr:02X}{tg:02X}{tb:02X}  n={n:7d}  bbox(px)={box}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
