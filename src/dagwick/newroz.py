"""Newroz for the whole Airflow UI, drawn with CSS only (used by the Newroz theme).

Dawn breaks behind three ranges of mountains along the bottom of the window, drawn
as fine ridgelines so the page shows through them. Bonfires burn on four peaks:
their flames flicker, their light breathes on the hillsides, sparks fly up from them
and glowing embers drift up across the whole window. A line of torches climbs the
hillside to one of the fires, as at Akre on Newroz eve. The Kurdish sun, with its
21 rays, turns slowly in the top-right corner and sends soft beams of dawn light
across the window. Nergiz (narcissus) and red tulips sway in the bottom
corners with a butterfly resting on each bunch.

Everything is drawn behind Airflow's page and ignores the mouse, so it never covers
Airflow's text, buttons, menus or sidebar. The images are still and CSS moves them
with transforms, fades or a few frames shown in turn, so the browser never redraws
them while they move; viewers who prefer reduced motion get a still scene.
"""

from __future__ import annotations

import math
import random
from typing import Any

from dagwick.scene import settle, url

SEED = 321  # 21 March

# Behind Airflow's page: the scene shows in the space Airflow leaves empty and never
# covers its text, buttons, menus or sidebar.
BEHIND = "-1"

SUN_RAYS = 21  # the sun on the Kurdish flag has 21 rays, for the 21st of March
GOLD = "#fbbf24"

W, H = 1200, 96  # one repeat of the mountains, in px; every layer below uses it
FLAME_FRAMES = 6
EMBER_H = 720  # px: one tile of the rising sparks and embers
SUN_SIZE = 190  # px
SUN_CENTRE = (SUN_SIZE * 0.2, SUN_SIZE * 0.14)  # px from the window's top-right corner
BEAM_W, BEAM_H = 1100, 760  # px: the dawn light fanning out from the sun

Point = tuple[float, float]

# (name, highest peak, lowest valley, points across one repeat): far to near.
RANGES = (("far", 18, 58, 9), ("mid", 34, 70, 7), ("near", 52, 84, 6))
LINES = {
    # range: (colour, opacity) of its outline; the near range catches the firelight
    "dark": {"far": ("#a7d3c2", 0.22), "mid": ("#a7d3c2", 0.36), "near": ("#fbbf24", 0.42)},
    "light": {"far": ("#3f7f68", 0.25), "mid": ("#3f7f68", 0.4), "near": ("#c2410c", 0.45)},
}


def ridge_points(rng: random.Random, top: float, bottom: float, count: int) -> list[Point]:
    """Peaks and valleys across one repeat; the ends meet so the repeats join."""
    step = W / count
    pts = []
    for i in range(count):
        high = i % 2 == 0
        y = rng.uniform(top, top + 12) if high else rng.uniform(bottom - 14, bottom)
        pts.append((i * step + rng.uniform(-step * 0.15, step * 0.15) if i else 0.0, y))
    pts.append((float(W), pts[0][1]))
    return pts


def smooth_line(pts: list[Point]) -> str:
    """A smooth line through the points (Catmull-Rom as Béziers)."""
    out = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    ext = [(pts[-2][0] - W, pts[-2][1]), *pts, (pts[1][0] + W, pts[1][1])]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(out)


def ranges() -> tuple[dict[str, list[Point]], list[tuple[float, float, float]]]:
    """The three ranges and the fires: (x, y, size), on peaks of all three ranges."""
    rng = random.Random(SEED)
    ridges = {name: ridge_points(rng, top, bottom, n) for name, top, bottom, n in RANGES}
    fires = []
    for name, size, picks in (("near", 1.4, (2, 4)), ("mid", 1.0, (6,)), ("far", 0.7, (4,))):
        for i in picks:
            x, y = ridges[name][i]
            fires.append((round(x), round(y + 1), size))
    return ridges, fires


def mountains_svg(theme: str) -> str:
    """One repeat of the three ranges as fine lines, and the fires' logs.

    Only the ridgelines are drawn, with a faint shade fading out beneath them, so the
    page shows through the mountains.
    """
    ridges, fires = ranges()
    defs, shapes = [], []
    for name, *_ in RANGES:
        colour, alpha = LINES[theme][name]
        line = smooth_line(ridges[name])
        defs.append(
            f"<linearGradient id='{name}' x1='0' y1='0' x2='0' y2='1'>"
            f"<stop offset='0' stop-color='{colour}' stop-opacity='{alpha / 4:.2f}'/>"
            f"<stop offset='.6' stop-color='{colour}' stop-opacity='0'/></linearGradient>"
        )
        shapes.append(
            f"<path d='{line} L{W} {H} L0 {H}Z' fill='url(#{name})'/>"
            f"<path d='{line}' fill='none' stroke='{colour}' stroke-opacity='{alpha}' "
            "stroke-width='1.4' stroke-linecap='round'/>"
        )
    logs = "".join(
        f"<path d='M{x - 6 * s:.1f} {y + 1.5 * s:.1f} L{x + 6 * s:.1f} {y - 0.5 * s:.1f} "
        f"M{x - 6 * s:.1f} {y - 0.5 * s:.1f} L{x + 6 * s:.1f} {y + 1.5 * s:.1f}' "
        f"stroke='#2a170c' stroke-width='{2.6 * s:.1f}' stroke-linecap='round'/>"
        for x, y, s in fires
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'>"
        f"<defs>{''.join(defs)}</defs>{''.join(shapes)}{logs}</svg>"
    )


def _tongue(height: float, width: float, lean: float, fill: str) -> str:
    """One tongue of flame, rising from (0, 0) and leaning by ``lean`` px at its tip."""
    h, w = height, width
    return (
        f"<path d='M{-w:.1f} 0 C{-w * 1.1:.1f} {-h * 0.35:.1f} {lean - w * 0.5:.1f} "
        f"{-h * 0.55:.1f} {lean:.1f} {-h:.1f} C{lean + w * 0.35:.1f} {-h * 0.6:.1f} "
        f"{w * 1.1:.1f} {-h * 0.35:.1f} {w:.1f} 0 C{w * 0.5:.1f} {h * 0.12:.1f} "
        f"{-w * 0.5:.1f} {h * 0.12:.1f} {-w:.1f} 0Z' fill='{fill}'/>"
    )


# Flame colours, bottom to top: outer, middle and the hot core.
FLAME_DEFS = (
    "<linearGradient id='o' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='#b91c1c'/>"
    "<stop offset='.45' stop-color='#ea580c'/><stop offset='1' stop-color='#f97316' "
    "stop-opacity='.85'/></linearGradient>"
    "<linearGradient id='m' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='#f97316'/>"
    "<stop offset='1' stop-color='#fbbf24'/></linearGradient>"
    "<linearGradient id='c' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='#fde68a'/>"
    "<stop offset='1' stop-color='#fffbeb'/></linearGradient>"
    "<radialGradient id='k'><stop offset='0' stop-color='#fde68a'/>"
    "<stop offset='.5' stop-color='#f97316'/><stop offset='1' stop-color='#7c2d12' "
    "stop-opacity='0'/></radialGradient>"
)


def flames_svg() -> str:
    """The flames in FLAME_FRAMES frames side by side, each slightly different: an outer
    flame, a brighter middle and a hot core, over glowing coals."""
    rng = random.Random(SEED + 1)
    _, fires = ranges()
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W * FLAME_FRAMES}' height='{H}'>"
        f"<defs>{FLAME_DEFS}</defs>"
    ]
    for frame in range(FLAME_FRAMES):
        for x, y, s in fires:
            tall = rng.uniform(0.88, 1.12)
            lean = rng.uniform(-3, 3) * s
            side = rng.choice((-1, 1))
            licks = (
                f"<g transform='translate({side * 5 * s:.1f} 0)'>"
                f"{_tongue(14 * s * rng.uniform(0.7, 1.15), 3.4 * s, side * 4 * s, 'url(#o)')}</g>"
                f"<g transform='translate({-side * 4 * s:.1f} 0)'>"
                f"{_tongue(10 * s * rng.uniform(0.6, 1.1), 2.6 * s, -side * 3 * s, 'url(#o)')}</g>"
            )
            body = (
                _tongue(26 * s * tall, 7.5 * s, lean, "url(#o)")
                + _tongue(18 * s * tall, 5 * s, lean * 0.8, "url(#m)")
                + _tongue(9 * s * tall, 2.6 * s, lean * 0.5, "url(#c)")
            )
            coals = (
                f"<ellipse cy='{1.2 * s:.1f}' rx='{9 * s:.1f}' ry='{2.6 * s:.1f}' fill='url(#k)'/>"
            )
            out.append(f"<g transform='translate({x + frame * W} {y})'>{coals}{licks}{body}</g>")
    out.append("</svg>")
    return "".join(out)


def glow_svg() -> str:
    """The firelight on the hillsides."""
    _, fires = ranges()
    spots = "".join(
        f"<ellipse cx='{x}' cy='{y - 6 * s:.0f}' rx='{60 * s:.0f}' ry='{34 * s:.0f}' "
        "fill='url(#g)'/>"
        for x, y, s in fires
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'>"
        "<defs><radialGradient id='g'><stop offset='0' stop-color='#fb923c' stop-opacity='.5'/>"
        "<stop offset='1' stop-color='#fb923c' stop-opacity='0'/></radialGradient></defs>"
        f"{spots}</svg>"
    )


def _segment(pts: list[Point], i: int) -> tuple[Point, Point, Point, Point]:
    """The Bézier from point ``i`` to ``i + 1`` of a ridge, as smooth_line draws it."""
    ext = [(pts[-2][0] - W, pts[-2][1]), *pts, (pts[1][0] + W, pts[1][1])]
    p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
    c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
    c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
    return p1, c1, c2, p2


def torches_svg() -> str:
    """One repeat of the mountains' band with a line of torches climbing the hillside
    to the fire on the middle range, as at Akre on Newroz eve (still: they flicker with
    the firelight's breathing)."""
    ridges, _ = ranges()
    (x0, y0), c1, c2, (x1, y1) = _segment(ridges["mid"], 5)  # valley up to the fire's peak
    face = 3.5  # just below the ridgeline, on the face of the hill
    count = 12
    torches = []
    for i in range(count):
        t, u = (i + 0.5) / count, 1 - (i + 0.5) / count
        px = u**3 * x0 + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * x1
        py = u**3 * y0 + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * y1
        torches.append(
            f"<circle cx='{px:.0f}' cy='{py + face:.0f}' r='4.5' fill='url(#tg)'/>"
            f"<circle cx='{px:.0f}' cy='{py + face:.0f}' r='.9' fill='#ffe3a3'/>"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'><defs>"
        "<radialGradient id='tg'><stop offset='0' stop-color='#fde68a'/>"
        "<stop offset='.35' stop-color='#fb923c' stop-opacity='.7'/>"
        "<stop offset='1' stop-color='#ea580c' stop-opacity='0'/></radialGradient></defs>"
        f"{''.join(torches)}</svg>"
    )


def sparks_svg() -> str:
    """One tile of small sparks above the fires (still: CSS moves the tile up)."""
    rng = random.Random(SEED + 2)
    _, fires = ranges()
    dots = []
    for x, _, s in fires:
        for _ in range(round(5 * s)):
            cx = (x + rng.gauss(0, 26)) % W
            dots.append(f"M{cx:.0f} {rng.uniform(0, EMBER_H):.0f}h0")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{EMBER_H}'>"
        f"<path d='{''.join(dots)}' stroke='#fdba74' stroke-width='2.4' "
        "stroke-linecap='round'/></svg>"
    )


def embers_svg() -> str:
    """One tile of bigger glowing embers drifting up from the fires (still: CSS moves
    the tile up, more slowly than the sparks)."""
    rng = random.Random(SEED + 3)
    _, fires = ranges()
    embers = []
    for i in range(14):
        x, _, _ = fires[i % len(fires)]
        cx, cy = (x + rng.gauss(0, 60)) % W, rng.uniform(0, EMBER_H)
        r = rng.uniform(1.4, 2.6)
        embers.append(
            f"<circle cx='{cx:.0f}' cy='{cy:.0f}' r='{r * 5:.1f}' fill='url(#eg)'/>"
            f"<circle cx='{cx:.0f}' cy='{cy:.0f}' r='{r:.1f}' fill='#ffd08a'/>"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{EMBER_H}'><defs>"
        "<radialGradient id='eg'><stop offset='0' stop-color='#fdba74' stop-opacity='.7'/>"
        "<stop offset='1' stop-color='#f97316' stop-opacity='0'/></radialGradient></defs>"
        f"{''.join(embers)}</svg>"
    )


def beams_svg() -> str:
    """Soft beams of dawn light fanning out from the sun in the corner (still: CSS
    makes them breathe)."""
    rng = random.Random(SEED + 6)
    cx, cy = BEAM_W - SUN_CENTRE[0], SUN_CENTRE[1]
    beams = []
    for i in range(7):
        a = math.radians(100 + i * 12 + rng.uniform(-4, 4))
        half = math.radians(rng.uniform(1.2, 2.6))
        far = BEAM_W * 1.1
        beams.append(
            f"M{cx} {cy} L{cx + far * math.cos(a - half):.0f} {cy + far * math.sin(a - half):.0f} "
            f"L{cx + far * math.cos(a + half):.0f} {cy + far * math.sin(a + half):.0f}Z"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{BEAM_W}' height='{BEAM_H}'>"
        f"<defs><radialGradient id='b' gradientUnits='userSpaceOnUse' cx='{cx}' cy='{cy}' "
        f"r='{BEAM_H * 0.95:.0f}'><stop offset='0' stop-color='#fde68a' stop-opacity='.16'/>"
        "<stop offset='.5' stop-color='#fde68a' stop-opacity='.06'/>"
        "<stop offset='1' stop-color='#fde68a' stop-opacity='0'/></radialGradient>"
        "<filter id='s' x='-20%' y='-20%' width='140%' height='140%'>"
        "<feGaussianBlur stdDeviation='7'/></filter></defs>"
        f"<path d='{' '.join(beams)}' fill='url(#b)' filter='url(#s)' opacity='.6'/></svg>"
    )


def sun_svg(size: int) -> str:
    """The Kurdish sun: a gold disc with 21 rays, and a soft halo."""
    c = size / 2
    inner, outer, disc = size * 0.25, size * 0.46, size * 0.2
    half = math.pi / SUN_RAYS / 2  # half the width of a ray at its base
    rays = []
    for i in range(SUN_RAYS):
        a = 2 * math.pi * i / SUN_RAYS - math.pi / 2
        pts = (
            (c + inner * math.cos(a - half), c + inner * math.sin(a - half)),
            (c + outer * math.cos(a), c + outer * math.sin(a)),
            (c + inner * math.cos(a + half), c + inner * math.sin(a + half)),
        )
        rays.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>"
        "<defs><radialGradient id='h'><stop offset='.3' stop-color='#fde68a' stop-opacity='.35'/>"
        "<stop offset='1' stop-color='#fde68a' stop-opacity='0'/></radialGradient>"
        "<radialGradient id='d'><stop offset='0' stop-color='#fde68a'/>"
        f"<stop offset='1' stop-color='{GOLD}'/></radialGradient>"
        "<radialGradient id='r'><stop offset='.5' stop-color='#fcd34d'/>"
        "<stop offset='1' stop-color='#f59e0b'/></radialGradient></defs>"
        f"<circle cx='{c}' cy='{c}' r='{c}' fill='url(#h)'/>"
        f"<path d='{' '.join(rays)}' fill='url(#r)'/>"
        f"<circle cx='{c}' cy='{c}' r='{disc:.1f}' fill='url(#d)'/></svg>"
    )


FLOWERS_W, FLOWERS_H = 220, 124

# The nergiz (Narcissus tazetta): front view of six cream tepals in two rings around a
# frilled gold cup, a side view and a closed bud; drawn once each and reused.
TEPAL = "M0 0 C-3.6 -1.6 -4.4 -6.2 -1.4 -9.6 C-.6 -10.4 .6 -10.4 1.4 -9.6 C4.4 -6.2 3.6 -1.6 0 0Z"


def _frill(r: float, bumps: int = 14, depth: float = 0.55) -> str:
    pts = []
    for i in range(bumps * 2):
        a = math.pi * i / bumps
        rr = r + (depth if i % 2 == 0 else -depth * 0.4)
        pts.append(f"{rr * math.cos(a):.1f} {rr * math.sin(a):.1f}")
    return "M" + " L".join(pts) + "Z"


FLOWER_DEFS = (
    "<radialGradient id='tp' cx='.5' cy='.95' r='1'><stop offset='0' stop-color='#e2e3b0'/>"
    "<stop offset='.3' stop-color='#fbf8ea'/>"
    "<stop offset='1' stop-color='#fff'/></radialGradient>"
    "<radialGradient id='tb' cx='.5' cy='.95' r='1'><stop offset='0' stop-color='#d4d4a2'/>"
    "<stop offset='.35' stop-color='#efe9d6'/>"
    "<stop offset='1' stop-color='#fbf8ef'/></radialGradient>"
    "<radialGradient id='cp'><stop offset='0' stop-color='#6b7a2a'/>"
    "<stop offset='.28' stop-color='#d6a20f'/><stop offset='.62' stop-color='#facc15'/>"
    "<stop offset='.9' stop-color='#f59e0b'/>"
    "<stop offset='1' stop-color='#ea7a0b'/></radialGradient>"
    "<linearGradient id='lf' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#4f7a5c'/>"
    "<stop offset='.5' stop-color='#7fa98a'/>"
    "<stop offset='1' stop-color='#5c8768'/></linearGradient>"
    "<linearGradient id='sp' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#e9dcb8'/>"
    "<stop offset='1' stop-color='#b9a678'/></linearGradient>"
    "<linearGradient id='cs' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#e2a90f'/>"
    "<stop offset='.7' stop-color='#facc15'/>"
    "<stop offset='1' stop-color='#f59e0b'/></linearGradient>"
    "<linearGradient id='bg' x1='0' y1='1' x2='0' y2='0'><stop offset='0' stop-color='#a9b77a'/>"
    "<stop offset='.55' stop-color='#ece6c4'/>"
    "<stop offset='1' stop-color='#fbf7e6'/></linearGradient>"
    "<linearGradient id='t' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#f87171'/>"
    "<stop offset='.5' stop-color='#dc2626'/>"
    "<stop offset='1' stop-color='#991b1b'/></linearGradient>"
    "<linearGradient id='tl' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#7ea86a'/>"
    "<stop offset='1' stop-color='#3f6a3c'/></linearGradient>"
    "<g id='fl'>"
    + "".join(
        f"<path d='{TEPAL}' transform='rotate({a})' fill='url(#tb)'/>" for a in (30, 150, 270)
    )
    + "".join(
        f"<path d='{TEPAL}' transform='rotate({a})' fill='url(#tp)' stroke='#e3d9bd' "
        "stroke-width='.25'/>"
        for a in (90, 210, 330)
    )
    + f"<path d='{_frill(3.1)}' fill='url(#cp)' stroke='#e0700a' stroke-width='.35'/>"
    "<circle r='1.25' fill='#55651f' opacity='.8'/></g>"
    "<g id='fs'>"
    + "".join(
        f"<path d='{TEPAL}' transform='scale(.42 1) rotate({a})' fill='url(#{f})'/>"
        for a, f in ((-125, "tb"), (125, "tb"), (180, "tb"), (-60, "tp"), (60, "tp"), (0, "tp"))
    )
    + "<path d='M-.4 -2.3 L3.6 -3.1 Q4 0 3.6 3.1 L-.4 2.3Z' fill='url(#cs)'/>"
    "<ellipse cx='3.6' rx='.9' ry='3.1' fill='#f59e0b'/></g>"
    "<g id='bd'><path d='M0 0 C-1.7 -1.4 -1.6 -5.2 0 -7.6 C1.6 -5.2 1.7 -1.4 0 0Z' "
    "fill='url(#bg)'/></g>"
)


def _strap(rng: random.Random, x: float, height: float, fill: str = "url(#lf)") -> str:
    """A long, flat strap leaf curving to one side, its tip rounded."""
    base = FLOWERS_H
    lean = rng.uniform(-1, 1) * height * 0.45
    w = rng.uniform(1.6, 2.4)
    tx, ty = x + lean, base - height
    cx, cy = x + lean * 0.1, base - height * 0.55
    return (
        f"<path d='M{x - w:.1f} {base} Q{cx - w:.1f} {cy:.1f} {tx - 0.4:.1f} {ty:.1f} "
        f"Q{tx + 0.6:.1f} {ty + 0.8:.1f} {tx + 0.6:.1f} {ty + 1.2:.1f} "
        f"Q{cx + w:.1f} {cy + 2:.1f} {x + w:.1f} {base}Z' fill='{fill}'/>"
    )


def _nergiz_stalk(rng: random.Random, x: float, height: float, scale: float) -> str:
    """A nergiz scape: an umbel of two to five flowers facing different ways on short
    stems, with a papery sheath at the top."""
    lean = rng.uniform(-5, 5)
    tx, ty = x + lean, FLOWERS_H - height
    out = [
        f"<path d='M{x:.1f} {FLOWERS_H} Q{x + lean * 0.2:.1f} {FLOWERS_H - height * 0.5:.1f} "
        f"{tx:.1f} {ty:.1f}' fill='none' stroke='#5d8a55' stroke-width='{1.4 * scale:.1f}' "
        "stroke-linecap='round'/>"
    ]
    count = rng.choice((2, 3, 3, 4, 5))
    heads = []
    for i in range(count):
        ang = -90 + (i - (count - 1) / 2) * rng.uniform(28, 40) + rng.uniform(-10, 10)
        ln = rng.uniform(4.5, 9) * scale
        hx = tx + ln * math.cos(math.radians(ang))
        hy = ty + ln * math.sin(math.radians(ang))
        out.append(
            f"<path d='M{tx:.1f} {ty:.1f} L{hx:.1f} {hy:.1f}' stroke='#6f9a5e' "
            f"stroke-width='{0.6 * scale:.1f}'/>"
        )
        s = scale * rng.uniform(0.6, 0.72)
        kind = rng.choices(("fl", "fs", "bd"), (0.65, 0.22, 0.13))[0]
        if kind == "fl":
            squash = rng.choice((1.0, 0.85, 0.7, 0.55))
            use = (
                f"<use href='#fl' transform='translate({hx:.1f} {hy:.1f}) "
                f"rotate({rng.uniform(-35, 35):.0f}) scale({s:.2f} {s * squash:.2f}) "
                f"rotate({rng.uniform(0, 60):.0f})'/>"
            )
        elif kind == "fs":
            use = (
                f"<use href='#fs' transform='translate({hx:.1f} {hy:.1f}) "
                f"rotate({ang + rng.uniform(-20, 20):.0f}) scale({s:.2f})'/>"
            )
        else:
            use = (
                f"<use href='#bd' transform='translate({hx:.1f} {hy:.1f}) "
                f"rotate({ang + 90:.0f}) scale({s * 0.9:.2f})'/>"
            )
        heads.append((hy, use))
    side = rng.choice((-1, 1))
    out.append(
        f"<path d='M{tx - 0.8:.1f} {ty + 1.5:.1f} Q{tx + side * 2:.1f} {ty - 3:.1f} "
        f"{tx + side * 5 * scale:.1f} {ty - 6 * scale:.1f} Q{tx + side * 2.5:.1f} {ty - 1:.1f} "
        f"{tx + 0.8:.1f} {ty + 2:.1f}Z' fill='url(#sp)'/>"
    )
    heads.sort(key=lambda h: -h[0])  # the lower flowers first, so the higher overlap them
    return "".join(out) + "".join(use for _, use in heads)


def _tulip_stalk(rng: random.Random, x: float, height: float, scale: float) -> str:
    """A red mountain tulip on a gently curved stem: two side petals and one in front."""
    lean = rng.uniform(-6, 6)
    tx, ty = x + lean, FLOWERS_H - height
    return (
        f"<path d='M{x:.1f} {FLOWERS_H} Q{x + lean * 0.1:.1f} {FLOWERS_H - height * 0.5:.1f} "
        f"{tx:.1f} {ty:.1f}' fill='none' stroke='#4d7c3a' stroke-width='1.5' "
        "stroke-linecap='round'/>"
        f"<g transform='translate({tx:.1f} {ty + 1:.1f}) rotate({lean * 1.5:.0f}) "
        f"scale({scale:.2f})'>"
        "<path d='M-5.5 -1 C-7 -7 -5 -12 -2.5 -14 C-2 -9 -1 -5 0 0Z' fill='url(#t)'/>"
        "<path d='M5.5 -1 C7 -7 5 -12 2.5 -14 C2 -9 1 -5 0 0Z' fill='url(#t)'/>"
        "<path d='M-4 0 C-5 -6 -2.5 -11 0 -13 C2.5 -11 5 -6 4 0 C2.5 1.5 -2.5 1.5 -4 0Z' "
        "fill='url(#t)'/><path d='M-1.5 -10 C-2.5 -7 -2.5 -4 -2 -1.5' fill='none' "
        "stroke='#fecaca' stroke-opacity='.6' stroke-width='.7' stroke-linecap='round'/></g>"
    )


BUTTERFLY = (
    # A small orange butterfly, its wings open, resting on the flowers.
    "<g fill='#f59e0b' stroke='#7c2d12' stroke-width='.4'>"
    "<path d='M0 0 C-3 -6 -8 -6 -7 -1 C-6 1 -3 1 0 0Z'/>"
    "<path d='M0 0 C3 -6 8 -6 7 -1 C6 1 3 1 0 0Z'/>"
    "<path d='M0 .4 C-2 3 -5 5 -4.5 2 C-4 1 -2 .6 0 .4Z' fill='#fbbf24'/>"
    "<path d='M0 .4 C2 3 5 5 4.5 2 C4 1 2 .6 0 .4Z' fill='#fbbf24'/></g>"
    "<path d='M0 -2 V3' stroke='#3b2414' stroke-width='1' stroke-linecap='round'/>"
)


def flowers_svg(seed: int) -> str:
    """A bunch of nergiz with their blue-green leaves and a few red mountain tulips, for a
    bottom corner of the window, with a butterfly resting on the tallest flower."""
    rng = random.Random(seed)
    leaves, stalks = [], []
    xs = sorted(rng.uniform(16, FLOWERS_W - 16) for _ in range(6))
    tallest = (0.0, float(FLOWERS_H))
    for i, x in enumerate(xs):
        for _ in range(rng.randint(2, 3)):
            leaves.append(_strap(rng, x + rng.uniform(-3, 3), rng.uniform(26, 70)))
        if i in (1, 4):
            leaves.append(_strap(rng, x + rng.uniform(-3, 3), rng.uniform(30, 50), "url(#tl)"))
            stalks.append(_tulip_stalk(rng, x, rng.uniform(46, 72), rng.uniform(1, 1.2)))
        else:
            height = rng.uniform(60, 104)
            stalks.append(_nergiz_stalk(rng, x, height, rng.uniform(1.1, 1.35)))
            tallest = min(tallest, (x, FLOWERS_H - height), key=lambda p: p[1])
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{FLOWERS_W}' height='{FLOWERS_H}'>"
        f"<defs>{FLOWER_DEFS}</defs>{''.join(leaves)}{''.join(stalks)}"
        f"<g transform='translate({tallest[0]:.0f} {tallest[1] - 9:.0f}) rotate(-12) scale(1.4)'>"
        f"{BUTTERFLY}</g></svg>"
    )


FLOWERS_LEFT = '[data-testid="main-content"]::before'
FLOWERS_RIGHT = '[data-testid="main-content"]::after'
MOVING = (
    "html::before",
    "html::after",
    "body::before",
    "body::after",
    "#root::before",
    FLOWERS_LEFT,
    FLOWERS_RIGHT,
)


def global_css() -> dict[str, Any]:
    """Newroz as Airflow theme ``globalCss`` (selector -> style).

    Every image is still: CSS moves the layers with transforms or opacity, which the
    browser does without redrawing them, and the flames step through a few frames, so
    the theme costs Airflow almost nothing.
    """
    layer = {"content": '""', "position": "fixed", "pointerEvents": "none", "zIndex": BEHIND}
    band = {
        **layer,
        "left": "0",
        "right": "0",
        "bottom": "0",
        "height": f"{H}px",
        "backgroundRepeat": "repeat-x",
        "backgroundPosition": "0 bottom",
        "backgroundSize": f"{W}px {H}px",
    }
    sun = SUN_SIZE
    flower_size = f"{FLOWERS_W}px {FLOWERS_H}px"
    flowers = {
        **layer,
        "bottom": "0",
        "width": f"{FLOWERS_W}px",
        "height": f"{FLOWERS_H}px",
        "backgroundSize": flower_size,
        "transformOrigin": "50% 100%",
    }
    css: dict[str, Any] = {
        # Sparks and embers rising from the fires and up off the top of the window
        # (painted first, under the hills). The layer is one tile taller than the window
        # and slides up by a tile, so the browser only moves it, never redraws it.
        "html::before": {
            **layer,
            "left": "0",
            "right": "0",
            "top": "0",
            "height": f"calc(100vh + {EMBER_H}px)",
            "backgroundImage": f"{url(sparks_svg())}, {url(embers_svg())}",
            "backgroundSize": f"{W}px {EMBER_H}px",
            "animation": "dagwickRise 36s linear infinite",
        },
        "@keyframes dagwickRise": {
            "from": {"transform": "translateY(0)"},
            "to": {"transform": f"translateY(-{EMBER_H}px)"},
        },
        "html.light::before": {"opacity": "0.7"},  # softer embers on a light page
        # Soft beams of dawn light from the sun, breathing.
        "body::before": {
            **layer,
            "top": "0",
            "right": "0",
            "width": f"{BEAM_W}px",
            "height": f"{BEAM_H}px",
            "backgroundImage": url(beams_svg()),
            "animation": "dagwickBeams 18s ease-in-out infinite",
        },
        "@keyframes dagwickBeams": {"50%": {"opacity": "0.45"}},
        # The sun in the corner, turning slowly.
        "#root::before": {
            **layer,
            "top": f"-{sun * 0.36:.0f}px",
            "right": f"-{sun * 0.3:.0f}px",
            "width": f"{sun}px",
            "height": f"{sun}px",
            "backgroundImage": url(sun_svg(sun)),
            "opacity": "0.6",
            "animation": "dagwickSun 180s linear infinite",
        },
        "html.light #root::before": {"opacity": "0.85"},
        "@keyframes dagwickSun": {
            "from": {"transform": "rotate(0deg)"},
            "to": {"transform": "rotate(360deg)"},
        },
        # The mountains, see-through enough that text behind them stays readable.
        "#root::after": {**band, "backgroundImage": url(mountains_svg("dark"))},
        "html.light #root::after": {"backgroundImage": url(mountains_svg("light"))},
        # Nergiz and red tulips in the bottom corners, swaying in the spring wind, each
        # with a butterfly resting on it.
        FLOWERS_LEFT: {
            **flowers,
            "left": "64px",
            "backgroundImage": url(flowers_svg(SEED + 3)),
            "animation": "dagwickSway 12s ease-in-out infinite",
        },
        FLOWERS_RIGHT: {
            **flowers,
            "right": "0",
            "backgroundImage": url(flowers_svg(SEED + 4)),
            "animation": "dagwickSway 14s ease-in-out -6s infinite",
        },
        "@keyframes dagwickSway": {
            "25%": {"transform": "rotate(-1.5deg)"},
            "75%": {"transform": "rotate(1.5deg)"},
        },
        # Firelight on the hillsides, breathing, and the torches climbing to a fire.
        "body::after": {
            **band,
            "backgroundImage": f"{url(torches_svg())}, {url(glow_svg())}",
            "animation": "dagwickGlow 4.8s ease-in-out infinite",
        },
        "@keyframes dagwickGlow": {"50%": {"opacity": "0.55"}},
        # The flames: a few still frames shown in turn, so they flicker.
        "html::after": {
            **band,
            "backgroundImage": url(flames_svg()),
            "backgroundSize": f"{W * FLAME_FRAMES}px {H}px",
            "animation": f"dagwickFlames 0.9s steps({FLAME_FRAMES}) infinite",
        },
        "@keyframes dagwickFlames": {
            "from": {"backgroundPosition": "0 bottom"},
            "to": {"backgroundPosition": f"-{W * FLAME_FRAMES}px bottom"},
        },
        "@media (prefers-reduced-motion: reduce)": {host: {"animation": "none"} for host in MOVING},
    }
    return settle(css)
