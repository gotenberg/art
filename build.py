#!/usr/bin/env python3
"""Pixel art for Gotenberg.

Run `python3 build.py` to regenerate the SVG and PNG files next to this
script. No dependency beyond the standard library.

Each piece is drawn on a 40 by 40 grid by a function taking a few parameters,
so its variants and animation frames share one drawing: press() for the
Gutenberg hand press, stamp() for litho's stamped sheet. PALETTE gives each
character its colour and "." is transparent. An animation is a list of
(frame, seconds); it is written as an SVG that cycles through its frames and
as a PNG sprite sheet.
"""
import struct
import zlib
from pathlib import Path

SIZE = 40            # pixels per side
SCALE = 16           # PNG export scale (40 px -> 640 px)
OUT = Path(__file__).resolve().parent

PALETTE = {
    "K": "#1c1917",  # ink outline
    "R": "#2a2522",  # rubber
    "H": "#3f3a36",  # iron
    "h": "#6b645d",  # iron highlight
    "W": "#ffffff",  # paper
    "g": "#a8a29e",  # printed text
    "O": "#8b5e3c",  # wood
    "o": "#5c3d24",  # wood shadow
    "w": "#b07d4f",  # wood highlight
    "X": "#b42318",  # printer's red: the seal
}

class Grid:
    def __init__(self):
        self.rows = [["."] * SIZE for _ in range(SIZE)]

    def put(self, x, y, ch):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.rows[y][x] = ch

    def hline(self, y, x0, x1, ch):
        for x in range(x0, x1 + 1):
            self.put(x, y, ch)

    def rect(self, x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            self.hline(y, x0, x1, ch)

    def outline(self, window, soft):
        """Ink outline around everything drawn, except inside `window`
        (x0, x1, y0, y1) where only the `soft` colours touch the background."""
        g = self.rows
        out = [r[:] for r in g]
        for y in range(SIZE):
            for x in range(SIZE):
                if g[y][x] != ".":
                    continue
                near = [g[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= x + dx < SIZE and 0 <= y + dy < SIZE]
                inside = window[0] <= x <= window[1] and window[2] <= y <= window[3]
                if any(c != "." for c in near) and not (inside and all(c in soft or c == "." for c in near)):
                    out[y][x] = "K"
        self.rows = out


WOOD = ("O", "w", "o")      # fill, highlight, shadow
IRON = ("H", "h")           # fill, highlight


def press(bar="right", platen=18, sheet="printed", phase=0):
    """The hand press seen head on: the sheet lies on the iron forme, on a
    long carriage bed, under the platen.

    bar: "right" (at rest), "front" (pulled toward the viewer) or "left"
    (swung across). platen: its top row, 15 when raised, 18 when down on the
    sheet. sheet: None, "blank" or "printed". phase flips the screw thread,
    to show it turning.
    """
    fill, light, dark = WOOD
    iron, shine = IRON
    g = Grid()
    # cap, cheeks, base
    g.rect(8, 3, 31, 6, fill); g.hline(3, 8, 31, light); g.hline(6, 8, 31, dark)
    for x0 in (9, 27):
        g.rect(x0, 7, x0 + 3, 35, fill); g.rect(x0, 7, x0, 35, light); g.rect(x0 + 3, 7, x0 + 3, 35, dark)
    g.rect(7, 34, 32, 36, fill); g.hline(34, 7, 32, light); g.hline(36, 7, 32, dark)
    # carriage bed and the forme on it
    g.rect(4, 27, 35, 29, fill); g.hline(27, 4, 35, light); g.hline(29, 4, 35, dark)
    g.rect(12, 25, 27, 26, iron); g.hline(25, 12, 27, shine)
    if sheet:
        g.rect(12, 21, 27, 24, "W")
        if sheet == "printed":
            for x in (14, 15, 16, 18, 19, 20, 21, 23, 24, 25):
                g.put(x, 22, "g")
            for x in (13, 14, 15, 17, 18, 19, 21, 22, 23, 25, 26):
                g.put(x, 24, "g")
    # platen, hose, nut and the screw running through it
    p = platen
    g.hline(p, 13, 26, shine); g.rect(13, p + 1, 26, p + 2, iron)
    g.rect(18, p - 2, 21, p - 1, iron)
    g.rect(16, 7, 23, 9, iron); g.hline(7, 16, 23, shine)
    for y in range(10, p - 2):
        g.hline(y, 19, 21, shine if (y + phase) % 2 == 0 else iron)
    # bar and knob
    sx = 20

    def seg(x0, x1, y):
        g.hline(y, x0, x1, fill); g.hline(y + 1, x0, x1, dark)

    def knob(x0, y0):
        g.rect(x0, y0, x0 + 2, y0 + 3, light)
        for x, y in ((x0, y0), (x0 + 2, y0), (x0, y0 + 3), (x0 + 2, y0 + 3)):
            g.put(x, y, fill)

    if bar == "right":
        for i in range(4):
            seg(sx + 2 + 3 * i, sx + 4 + 3 * i, 12 + i)
        seg(sx + 14, sx + 15, 16); knob(sx + 15, 15)
    elif bar == "left":
        for i in range(4):
            seg(sx - 4 - 3 * i, sx - 2 - 3 * i, 12 + i)
        seg(sx - 15, sx - 14, 16); knob(sx - 17, 15)
    else:
        g.rect(sx - 1, 13, sx + 1, 14, dark)
        g.rect(sx - 2, 15, sx + 2, 18, light)
        for x, y in ((sx - 2, 15), (sx + 2, 15), (sx - 2, 18), (sx + 2, 18)):
            g.put(x, y, fill)
    g.outline((13, 26, 7, 26), set(WOOD))
    return g.rows


def dashes(g, y, x0, x1, ch="g", phase=0):
    """A line of text from x0 to x1: dashes of 3, 4, 2 and 3 with single gaps."""
    pattern = (3, 1, 4, 1, 2, 1, 3, 1)
    x, i = x0, phase
    while x <= x1:
        n = pattern[i % len(pattern)]
        if i % 2 == 0:
            g.hline(y, x, min(x1, x + n - 1), ch)
        x += n
        i += 1


def ring(g, cx, cy, r_out, r_in, ch):
    for y in range(SIZE):
        for x in range(SIZE):
            d = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
            if r_in * r_in <= d <= r_out * r_out:
                g.put(x, y, ch)


def stamp(die=18, sealed=True):
    """A printed sheet and the rubber stamp that seals it, held above the seal.

    die: the top row of the rubber die, 18 when the stamp is held high, 22
    when it is pressed on the sheet. sealed: whether the seal is on the sheet.
    """
    fill, light, dark = WOOD
    g = Grid()
    # the sheet, with its lines of text
    g.rect(3, 7, 30, 38, "W")
    for k, y in enumerate(range(11, 36, 3)):
        dashes(g, y, 6, 27, phase=(k % 2) * 2)
    if sealed:
        ring(g, 23.5, 30.5, 6.5, 4.6, "X"); ring(g, 23.5, 30.5, 4.6, 0, "W")
        for x, y in ((20, 30), (21, 31), (22, 32), (23, 31), (24, 30), (25, 29), (26, 28)):
            g.put(x, y, "X")
    # the stamp: knob, neck and flared handle, which squash a pixel onto the
    # wooden mount when pressed; the rubber die shows its inked face only in the air
    pressed = die >= 22
    d = die
    h = d + (1 if pressed else 0)
    g.hline(h - 14, 21, 25, light); g.rect(20, h - 13, 26, h - 12, fill); g.rect(20, h - 13, 20, h - 12, light)
    g.hline(h - 11, 21, 25, dark)
    g.rect(22, h - 10, 24, h - 7, fill); g.rect(24, h - 10, 24, h - 7, dark)
    for i, (x0, x1) in enumerate(((20, 26), (19, 27), (18, 28))):
        g.hline(h - 6 + i, x0, x1, fill); g.put(x0, h - 6 + i, light)
    g.rect(16, d - 3, 30, d - 1, fill); g.hline(d - 3, 16, 30, light); g.hline(d - 1, 16, 30, dark)
    g.rect(17, d, 29, d + 1, "R")
    if not pressed:
        g.hline(d + 2, 18, 28, "X")
    g.outline((-1, -1, -1, -1), set())
    # centre the composition in the frame: three cells right, one up
    return [[g.rows[y + 1][x - 3] if 0 <= x - 3 < SIZE and y + 1 < SIZE else "." for x in range(SIZE)] for y in range(SIZE)]


PIECES = {
    "press": lambda: press(),
    "litho-logo": lambda: stamp(),
}

ANIMATIONS = {
    # a sheet goes in blank, the bar swings across, the sheet comes out printed
    "press-animated": [
        (press(platen=15, sheet="blank"), 0.7),
        (press(bar="front", platen=16, sheet="blank", phase=1), 0.25),
        (press(bar="left", platen=18, sheet="blank"), 0.6),
        (press(bar="front", platen=16, phase=1), 0.25),
        (press(platen=15), 1.0),
        (press(platen=15, sheet=None), 0.3),
    ],
    # the stamp comes down on a fresh sheet and lifts away from the seal
    "litho-logo-animated": [
        (stamp(sealed=False), 0.7),
        (stamp(die=20, sealed=False), 0.15),
        (stamp(die=22, sealed=False), 0.5),
        (stamp(die=20), 0.15),
        (stamp(), 1.3),
    ],
}


def paths(grid):
    runs = {}
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            ch = row[x]
            start = x
            while x < len(row) and row[x] == ch:
                x += 1
            if ch != ".":
                runs.setdefault(PALETTE[ch], []).append(f"M{start} {y}h{x - start}v1h-{x - start}z")
    return "\n".join(f'  <path fill="{color}" d="{"".join(d)}"/>' for color, d in runs.items())


FULL = (0, 0, SIZE, SIZE)


def bounds(grids):
    """The box (x, y, width, height) holding every drawn pixel of the grids."""
    xs = [x for g in grids for row in g for x, ch in enumerate(row) if ch != "."]
    ys = [y for g in grids for y, row in enumerate(g) for ch in row if ch != "."]
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def svg_open(box):
    x, y, w, h = box
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
            f'width="{w * SCALE}" height="{h * SCALE}" shape-rendering="crispEdges">\n')


def svg(grid, box=FULL):
    return svg_open(box) + paths(grid) + "\n</svg>\n"


def svg_animated(frames, box=FULL):
    total = sum(seconds for _, seconds in frames)
    css = [f".f{{opacity:0;animation:{total:g}s step-end infinite}}"]
    groups = []
    t = 0
    for i, (grid, seconds) in enumerate(frames):
        a, b = 100 * t / total, 100 * (t + seconds) / total
        css.append(f".f{i}{{animation-name:f{i}}}@keyframes f{i}{{0%{{opacity:0}}{a:.3f}%{{opacity:1}}{b:.3f}%{{opacity:0}}}}")
        groups.append(f'<g class="f f{i}">\n{paths(grid)}\n</g>')
        t += seconds
    css.append("@media(prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}}")
    return svg_open(box) + "<style>" + "".join(css) + "</style>\n" + "\n".join(groups) + "\n</svg>\n"


def png(grid, box=FULL):
    x0, y0, w, h = box
    grid = [row[x0:x0 + w] for row in grid[y0:y0 + h]]

    def rgba(ch):
        if ch == ".":
            return b"\0\0\0\0"
        c = PALETTE[ch]
        return bytes(int(c[i:i + 2], 16) for i in (1, 3, 5)) + b"\xff"

    raw = b"".join(
        (b"\0" + b"".join(rgba(ch) * SCALE for ch in row)) * SCALE for row in grid
    )

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    width, height = len(grid[0]) * SCALE, len(grid) * SCALE
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


# Pieces written trimmed to their ink instead of the full square. The press
# keeps the square: gotenberg.dev sizes it by the 40 px grid.
TRIMMED = {"litho-logo", "litho-logo-animated"}

if __name__ == "__main__":
    for name, draw in PIECES.items():
        grid = draw()
        box = bounds([grid]) if name in TRIMMED else FULL
        (OUT / f"{name}.svg").write_text(svg(grid, box))
        (OUT / f"{name}.png").write_bytes(png(grid, box))
        print(name, box)
    for name, frames in ANIMATIONS.items():
        box = bounds([grid for grid, _ in frames]) if name in TRIMMED else FULL
        (OUT / f"{name}.svg").write_text(svg_animated(frames, box))
        x0, y0, w, h = box
        sheet = [sum((grid[y][x0:x0 + w] for grid, _ in frames), []) for y in range(y0, y0 + h)]
        (OUT / f"{name}.png").write_bytes(png(sheet, (0, 0, w * len(frames), h)))
        print(name, box, f"({len(frames)} frames)")
