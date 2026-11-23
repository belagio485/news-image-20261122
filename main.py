#!/usr/bin/env python3
"""news-image-20261122: one front page summing up Sunday 22 November 2026.

Draws a 1024x1024 newspaper front page with six verified stories from
22 November 2026 (Reuters / Associated Press), using only the Python
standard library. No network access. The output is fully deterministic:
the same bytes are written on every run.

Stories (all reported on 22 November 2026):
  1. COP31 climate talks in Antalya collapse with no deal on fossil fuels.
  2. Israeli settlers torch homes and cars in West Bank villages; Gadi
     Eisenkot condemns the attacks as "Jewish terrorism".
  3. Two tankers struck near the Strait of Hormuz; Bahrain reports an
     Iranian attack and two people hurt.
  4. Candy factory fire in Cikande, West Java: 3 dead, 37 unaccounted for.
  5. Explosion damages a Russian ship docked at Benghazi, Libya;
     officials blame suspected Ukrainian sea drones.
  6. Markets: the S&P 500 falls 3.7% into a correction as the AI
     sell-off deepens.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (22, 22, 22)
NAVY = (20, 33, 61)
RED = (178, 34, 34)
ORANGE = (214, 110, 24)
GOLD = (201, 162, 39)
STEEL = (90, 110, 140)
LIGHT_STEEL = (176, 196, 214)
GREY = (110, 105, 92)
WHITE = (255, 255, 255)
GREEN = (46, 125, 50)

# ---------------------------------------------------------------- canvas

PIX = bytearray(W * H * 3)


def fill(c):
    PIX[0:len(PIX)] = bytes(c) * (W * H)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i] = c[0]
        PIX[i + 1] = c[1]
        PIX[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        PIX[i:i + (x1 - x0) * 3] = row


def hline(x, y, length, c, thick=1):
    rect(x, y, length, thick, c)


def vline(x, y, length, c, thick=1):
    rect(x, y, thick, length, c)


def frame(x, y, w, h, c, thick=1):
    hline(x, y, w, c, thick)
    hline(x, y + h - thick, w, c, thick)
    vline(x, y, h, c, thick)
    vline(x + w - thick, y, h, c, thick)


def line(x0, y0, x1, y1, c, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        rect(x0 - thick // 2, y0 - thick // 2, thick, thick, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, filled=False):
    if filled:
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            hline(cx - dx, cy + dy, 2 * dx + 1, c)
    else:
        steps = max(24, int(2 * math.pi * r))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            put(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)


def poly(points, c, filled=False):
    if filled:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            xs_at = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs_at.append(int(x0 + t * (x1 - x0)))
            xs_at.sort()
            for j in range(0, len(xs_at) - 1, 2):
                hline(xs_at[j], yy, xs_at[j + 1] - xs_at[j], c)
    else:
        n = len(points)
        for i in range(n):
            line(points[i][0], points[i][1],
                 points[(i + 1) % n][0], points[(i + 1) % n][1], c)


# ---------------------------------------------------------------- 5x7 font

def _g(*rows):
    return rows


FONT = {
    "A": _g("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": _g("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": _g("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": _g("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": _g("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": _g("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": _g("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": _g("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": _g("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": _g("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": _g("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": _g("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": _g("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": _g("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": _g("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": _g("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": _g("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": _g("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": _g("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": _g("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": _g("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": _g("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": _g("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": _g("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": _g("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": _g("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": _g("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": _g("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": _g("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": _g("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": _g("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": _g("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": _g("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": _g("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": _g("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": _g("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": _g("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": _g("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": _g("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": _g("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": _g("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": _g("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": _g("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": _g("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': _g("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": _g("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": _g("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": _g("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": _g("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": _g("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": _g("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": _g("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": _g("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": _g("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "_": _g("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "*": _g("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "#": _g("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": _g("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": _g("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": _g("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": _g("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": _g("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

BLANK = ("00000",) * 7


def norm(s):
    s = s.upper()
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u00b7", ".")
    return "".join(ch if ch in FONT else " " for ch in s)


def text_w(s, scale):
    return len(norm(s)) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    s = norm(s)
    cx = x
    for ch in s:
        glyph = FONT.get(ch, BLANK)
        for r in range(7):
            row = glyph[r]
            for c in range(5):
                if row[c] == "1":
                    rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_center(cx, y, s, scale, color):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    s = norm(s)
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_block(x, y, s, scale, max_w, color, leading=6):
    lines = wrap(s, scale, max_w)
    yy = y
    for ln in lines:
        draw_text(x, yy, ln, scale, color)
        yy += 7 * scale + leading
    return yy


# ---------------------------------------------------------------- icons

def draw_globe(cx, cy, r):
    circle(cx, cy, r, STEEL, filled=True)
    circle(cx, cy, r, NAVY)
    for k in range(-2, 3):
        yy = cy + k * r // 3
        half = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
        hline(cx - half, yy, 2 * half, LIGHT_STEEL)
    for k in (-1, 0, 1):
        rx = r * 2 // 3 if k == 0 else r // 3
        for a in range(0, 360, 4):
            ang = math.radians(a)
            put(int(cx + rx * math.cos(ang)), int(cy + r * math.sin(ang)),
                LIGHT_STEEL)
    # land blobs
    circle(cx - r // 3, cy - r // 4, r // 4, GREEN, filled=True)
    circle(cx + r // 3, cy + r // 5, r // 5, GREEN, filled=True)
    circle(cx + r // 8, cy - r // 2, r // 6, GREEN, filled=True)
    # red crack: the deal breaking
    line(cx - r // 2, cy + r // 2, cx - r // 6, cy + r // 6, RED, 4)
    line(cx - r // 6, cy + r // 6, cx + r // 8, cy + r // 3, RED, 4)
    line(cx + r // 8, cy + r // 3, cx + r // 2, cy - r // 6, RED, 4)


def draw_flame(cx, cy, s):
    pts = [(cx, cy - 3 * s), (cx + 2 * s, cy - s), (cx + s, cy + 2 * s),
           (cx - s, cy + 2 * s), (cx - 2 * s, cy - s)]
    poly(pts, ORANGE, filled=True)
    pts2 = [(cx, cy - s), (cx + s, cy + s), (cx, cy + 2 * s),
            (cx - s, cy + s)]
    poly(pts2, GOLD, filled=True)


def draw_factory(cx, cy, s):
    # s = half width of the building
    rect(cx - 2 * s, cy - s, 4 * s, 2 * s, INK)
    poly([(cx - 2 * s, cy - s), (cx - s, cy - 2 * s),
          (cx, cy - s), (cx + s, cy - 2 * s),
          (cx + 2 * s, cy - s)], INK, filled=True)
    rect(cx + s, cy - 3 * s, s // 2, 2 * s, INK)
    circle(cx + s + s // 4, cy - 3 * s - 4, 5, GREY, filled=True)
    circle(cx + s + s // 4 + 8, cy - 3 * s - 12, 7, GREY, filled=True)
    rect(cx - 2 * s, cy + s, 4 * s, s // 3, RED)


def draw_tanker(cx, cy, s):
    # hull
    poly([(cx - 3 * s, cy), (cx + 3 * s, cy), (cx + 2 * s, cy + s),
          (cx - 2 * s, cy + s)], INK, filled=True)
    # deck tanks
    rect(cx - 2 * s, cy - s, s, s, STEEL)
    rect(cx - s // 2, cy - s, s, s, STEEL)
    rect(cx + s, cy - s, s, s, STEEL)
    # smoke from a strike
    circle(cx + 2 * s, cy - 2 * s, 6, GREY, filled=True)
    circle(cx + 2 * s + 8, cy - 2 * s - 8, 8, GREY, filled=True)
    # waves
    for k in range(-2, 3):
        line(cx + k * s - s // 2, cy + 2 * s, cx + k * s + s // 2,
             cy + 2 * s, STEEL, 3)


def draw_ship(cx, cy, s):
    poly([(cx - 3 * s, cy), (cx + 3 * s, cy), (cx + 2 * s, cy + s),
          (cx - 2 * s, cy + s)], NAVY, filled=True)
    vline(cx, cy - 3 * s, 3 * s, INK, 3)
    poly([(cx, cy - 3 * s), (cx + 2 * s, cy - 2 * s), (cx, cy - s)],
         RED, filled=True)
    for k in range(-2, 3):
        line(cx + k * s - s // 2, cy + 2 * s, cx + k * s + s // 2,
             cy + 2 * s, STEEL, 3)


def draw_chart(x, y, w, h):
    frame(x, y, w, h, GREY, 1)
    # falling line: S&P 500 -3.7%
    pts = [(x + 8, y + 12), (x + w // 3, y + h // 3),
           (x + 2 * w // 3, y + h // 2), (x + w - 8, y + h - 12)]
    for a, b in zip(pts, pts[1:]):
        line(a[0], a[1], b[0], b[1], RED, 4)
    for p in pts:
        circle(p[0], p[1], 4, RED, filled=True)
    # bars at the bottom
    bw = (w - 16) // 5
    heights = [h // 4, h // 3, h // 5, h // 6, h // 8]
    for i, hh in enumerate(heights):
        rect(x + 8 + i * bw, y + h - 6 - hh, bw - 4, hh, LIGHT_STEEL)


# ---------------------------------------------------------------- layout

def story_cell(x, y, w, h, kicker, headline, body, icon):
    frame(x, y, w, h, INK, 2)
    ix, iy = x + 58, y + 92
    icon(ix, iy, 22)
    tx = x + 132
    draw_text(tx, y + 16, kicker, 2, RED)
    draw_block(tx, y + 40, headline, 3, w - 150, INK, leading=4)
    n_head = len(wrap(headline, 3, w - 150))
    by = y + 40 + n_head * (7 * 3 + 4) + 6
    draw_block(tx, by, body, 2, w - 150, INK, leading=5)


def main():
    fill(PAPER)
    frame(16, 16, 992, 992, INK, 3)
    frame(26, 26, 972, 972, INK, 1)

    # masthead
    rect(28, 28, 968, 118, NAVY)
    draw_center(512, 62, "THE WORLD IN ONE DAY", 7, WHITE)
    draw_text(48, 118, "NO. 326", 2, GOLD)
    draw_text(1024 - 48 - text_w("PRICE: ONE DAY", 2), 118,
              "PRICE: ONE DAY", 2, GOLD)

    # dateline
    draw_center(512, 158, "SUNDAY, 22 NOVEMBER 2026", 3, RED)
    draw_center(512, 186, "SIX STORIES FROM AROUND THE WORLD", 2, GREY)
    hline(36, 208, 952, INK, 2)

    # ---- lead story: COP31
    draw_text(40, 226, "CLIMATE - COP31 - ANTALYA, TURKEY", 2, RED)
    draw_text(40, 252, "CLIMATE TALKS", 5, INK)
    draw_text(40, 292, "COLLAPSE", 5, INK)
    draw_block(40, 340, "COP31 climate talks in Antalya, Turkey, end "
               "without a final deal after overtime negotiations "
               "break down over fossil fuels.", 2, 560, INK, leading=5)
    draw_block(40, 412, "The closing draft drew objections from the EU "
               "and vulnerable nations.", 2, 560, GREY, leading=5)

    # globe icon beside the lead
    draw_globe(668, 330, 62)
    draw_text(620, 404, "NO DEAL", 3, RED)

    # markets box
    frame(772, 224, 216, 216, INK, 2)
    draw_text(788, 238, "MARKETS", 2, RED)
    draw_text(788, 264, "S&P 500", 2, INK)
    draw_text(788, 288, "-3.7%", 5, RED)
    draw_chart(788, 336, 184, 56)
    draw_block(788, 400, "AI SELL-OFF DEEPENS.",
               2, 184, INK, leading=4)

    hline(36, 456, 952, INK, 2)

    # ---- four stories, 2 x 2 grid
    story_cell(36, 470, 464, 236, "WEST BANK",
               "SETTLERS TORCH HOMES IN WEST BANK",
               "12 vehicles burned overnight. Opposition leader "
               "Eisenkot calls the attacks 'Jewish terrorism'.",
               draw_flame)
    story_cell(524, 470, 464, 236, "STRAIT OF HORMUZ",
               "TWO TANKERS STRUCK NEAR HORMUZ",
               "Two tankers hit near the Strait of Hormuz. Bahrain "
               "reports an Iranian attack; two people hurt.",
               draw_tanker)
    story_cell(36, 720, 464, 236, "INDONESIA - WEST JAVA",
               "FACTORY FIRE: 3 DEAD, 37 MISSING",
               "Blaze at a candy factory in Cikande, West Java. "
               "Three workers dead, 37 unaccounted for.",
               draw_factory)
    story_cell(524, 720, 464, 236, "LIBYA - BENGHAZI",
               "RUSSIAN SHIP HIT AT BENGHAZI",
               "Explosion damages a Russian ship docked at Benghazi. "
               "Libya blames suspected Ukrainian sea drones.",
               draw_ship)

    # footer
    hline(36, 968, 952, INK, 1)
    draw_center(512, 978,
                "REPORTED ON SUNDAY 22 NOVEMBER 2026 - SOURCES: "
                "REUTERS, ASSOCIATED PRESS", 2, GREY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    write_png(path)
    print("wrote", path)


def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        i = yy * W * 3
        raw += PIX[i:i + W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
