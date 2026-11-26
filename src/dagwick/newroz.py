"""Newroz for the whole Airflow UI, drawn with CSS only (used by the Newroz theme).

Dawn breaks behind three ranges of mountains along the bottom of the window, drawn
as fine ridgelines so the page shows through them. Bonfires burn on four peaks:
their flames flicker, their light breathes on the hillsides and sparks rise from
them. Nergiz (narcissus) and red tulips sway in the bottom corners, and the Kurdish
sun, with its 21 rays, turns slowly in the top-right corner.

Everything is drawn above the page but ignores the mouse, stays below Airflow's menus
and dialogs, and leaves the sidebar on top. Movement uses CSS transforms, fades or a
few still frames, and viewers who prefer reduced motion get a still scene.
"""

from __future__ import annotations

import math
import random
from typing import Any

from dagwick.snow import url

SEED = 321  # 21 March

# Above Airflow's content but below its menus and dialogs (Chakra puts those at 1400+);
# Airflow's sidebar is lifted just above the decorations so they never cover it.
TOP = "1000"
SIDEBAR = "1001"

SUN_RAYS = 21  # the sun on the Kurdish flag has 21 rays, for the 21st of March
GOLD = "#fbbf24"

W, H = 1200, 96  # one repeat of the mountains, in px; every layer below uses it
FLAME_FRAMES = 4
SPARK_H = 640  # one repeat of the rising sparks, in px

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
        f"<path d='M{x - 8 * s:.1f} {y + 2 * s:.1f} L{x + 8 * s:.1f} {y - 1 * s:.1f} "
        f"M{x - 8 * s:.1f} {y - 1 * s:.1f} L{x + 8 * s:.1f} {y + 2 * s:.1f}' "
        f"stroke='#3b2416' stroke-width='{2.2 * s:.1f}' stroke-linecap='round'/>"
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
        f"<path d='M{-w:.1f} 0 C{-w:.1f} {-h * 0.45:.1f} {lean - w * 0.2:.1f} {-h * 0.6:.1f} "
        f"{lean:.1f} {-h:.1f} C{lean + w * 0.2:.1f} {-h * 0.6:.1f} {w:.1f} {-h * 0.45:.1f} "
        f"{w:.1f} 0Z' fill='{fill}'/>"
    )


def flames_svg() -> str:
    """The flames in FLAME_FRAMES frames side by side, each slightly different."""
    rng = random.Random(SEED + 1)
    _, fires = ranges()
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W * FLAME_FRAMES}' height='{H}'>"]
    for frame in range(FLAME_FRAMES):
        for x, y, s in fires:
            tall = rng.uniform(0.85, 1.15)
            lean = rng.uniform(-3, 3) * s
            tongues = (
                _tongue(24 * s * tall, 7 * s, lean, "#ea580c")
                + _tongue(17 * s * tall, 5 * s, lean * 0.8, "#f59e0b")
                + _tongue(9 * s * tall, 3 * s, lean * 0.5, "#fef3c7")
            )
            side = rng.choice((-1, 1))
            lick = (
                f"<g transform='translate({side * 5 * s:.1f} 0)'>"
                f"{_tongue(13 * s * rng.uniform(0.7, 1.2), 3.5 * s, side * 3 * s, '#f97316')}</g>"
            )
            out.append(f"<g transform='translate({x + frame * W} {y})'>{lick}{tongues}</g>")
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


def sparks_svg() -> str:
    """One repeat of sparks, gathered above the fires and spreading as they rise."""
    rng = random.Random(SEED + 2)
    _, fires = ranges()
    dots = []
    for x, _, s in fires:
        for _ in range(round(6 * s)):
            y = rng.uniform(0, SPARK_H)
            spread = 10 + (SPARK_H - y) * 0.08  # wider the higher they are
            cx = (x + rng.gauss(0, spread)) % W
            r, op = rng.uniform(0.9, 1.9), rng.uniform(0.5, 0.95)
            dots.append(
                f"<circle cx='{cx:.0f}' cy='{y:.0f}' r='{r:.1f}' fill='url(#e)' "
                f"opacity='{op:.2f}'/>"
            )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{SPARK_H}'>"
        "<defs><radialGradient id='e'><stop offset='0' stop-color='#fff7d6'/>"
        "<stop offset='.45' stop-color='#fb923c'/>"
        "<stop offset='1' stop-color='#f97316' stop-opacity='0'/></radialGradient></defs>"
        f"{''.join(dots)}</svg>"
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
        f"<stop offset='1' stop-color='{GOLD}'/></radialGradient></defs>"
        f"<circle cx='{c}' cy='{c}' r='{c}' fill='url(#h)'/>"
        f"<path d='{' '.join(rays)}' fill='{GOLD}'/>"
        f"<circle cx='{c}' cy='{c}' r='{disc:.1f}' fill='url(#d)'/></svg>"
    )


FLOWERS_W, FLOWERS_H = 132, 58
STEM = "#4d7c4f"


def _stem(x: float, top: float, bend: float) -> str:
    return (
        f"<path d='M{x:.1f} {FLOWERS_H} Q{x + bend:.1f} {(FLOWERS_H + top) / 2:.1f} "
        f"{x:.1f} {top:.1f}' fill='none' stroke='{STEM}' stroke-width='1.6' "
        "stroke-linecap='round'/>"
    )


def _leaf(x: float, side: int, length: float) -> str:
    tip = x + side * length * 0.45
    return (
        f"<path d='M{x:.1f} {FLOWERS_H} Q{x + side * 2:.1f} {FLOWERS_H - length * 0.6:.1f} "
        f"{tip:.1f} {FLOWERS_H - length:.1f} Q{x + side * length * 0.2:.1f} "
        f"{FLOWERS_H - length * 0.4:.1f} {x + side * 3:.1f} {FLOWERS_H}Z' fill='#5f8f52'/>"
    )


def nergiz(x: float, y: float, s: float) -> str:
    """A narcissus (nêrgiz), the flower of Kurdish spring: six white petals, a gold cup."""
    petals = "".join(
        f"<ellipse cx='0' cy='{-4.2 * s:.1f}' rx='{2.6 * s:.1f}' ry='{4.4 * s:.1f}' "
        f"transform='rotate({a})' fill='#fffdf5' stroke='#d9c78f' stroke-width='.6'/>"
        for a in range(0, 360, 60)
    )
    return (
        f"<g transform='translate({x:.1f} {y:.1f})'>{petals}"
        f"<circle r='{2.6 * s:.1f}' fill='#f59e0b'/><circle r='{1.3 * s:.1f}' fill='#fde047'/></g>"
    )


def tulip(x: float, y: float, s: float) -> str:
    """A red mountain tulip."""
    return (
        f"<g transform='translate({x:.1f} {y:.1f}) scale({s:.2f})'>"
        "<path d='M-5 -2 C-6 -9 -4 -13 -3 -14 L-1 -10 L0 -15 L1 -10 L3 -14 C4 -13 6 -9 5 -2 "
        "C4 1 -4 1 -5 -2Z' fill='#dc2626'/>"
        "<path d='M0 -15 L1 -10 L3 -14 C4 -13 6 -9 5 -2 C4 1 1 1 0 0Z' fill='#b91c1c'/></g>"
    )


def flowers_svg(seed: int) -> str:
    """A small bunch of nergiz and red tulips, for a bottom corner of the window."""
    rng = random.Random(seed)
    parts, heads = [], []
    for i in range(5):
        x = 14 + i * 26 + rng.uniform(-4, 4)
        top = rng.uniform(12, 30)
        parts.append(_stem(x, top, rng.uniform(-4, 4)))
        parts.append(_leaf(x, rng.choice((-1, 1)), rng.uniform(14, 24)))
        s = rng.uniform(0.75, 0.9)
        heads.append(nergiz(x, top, s) if i % 3 != 1 else tulip(x, top + 4, s))
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{FLOWERS_W}' height='{FLOWERS_H}'>"
        f"{''.join(parts)}{''.join(heads)}</svg>"
    )


FLOWERS_LEFT = '[data-testid="main-content"]::before'
FLOWERS_RIGHT = '[data-testid="main-content"]::after'
MOVING = (
    "html::before",
    "html::after",
    "body::after",
    "#root::before",
    FLOWERS_LEFT,
    FLOWERS_RIGHT,
)


def global_css() -> dict[str, Any]:
    """Newroz as Airflow theme ``globalCss`` (selector -> style)."""
    layer = {"content": '""', "position": "fixed", "pointerEvents": "none", "zIndex": TOP}
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
    sun = 190
    flowers = {
        **layer,
        "bottom": "0",
        "width": f"{FLOWERS_W}px",
        "height": f"{FLOWERS_H}px",
        "transformOrigin": "50% 100%",
        "willChange": "transform",
    }
    return {
        # Sparks rising from the fires (painted first, so the hills cover their start).
        "html::before": {
            **layer,
            "left": "0",
            "right": "0",
            "top": "0",
            "bottom": f"-{SPARK_H}px",
            "backgroundImage": url(sparks_svg()),
            "backgroundSize": f"{W}px {SPARK_H}px",
            "willChange": "transform",
            "animation": "dagwickSparks 26s linear infinite",
        },
        "@keyframes dagwickSparks": {
            "from": {"transform": "translate3d(0, 0, 0)"},
            "to": {"transform": f"translate3d(0, -{SPARK_H}px, 0)"},
        },
        # A warm dawn behind the hills, and spring green at the foot of the page.
        "body::before": {
            **layer,
            "left": "0",
            "right": "0",
            "bottom": "0",
            "height": "180px",
            "backgroundImage": "radial-gradient(ellipse 70% 100% at 50% 100%, "
            "rgba(251, 146, 60, 0.12), transparent 70%)",
        },
        # The sun in the corner, turning slowly.
        "#root::before": {
            **layer,
            "top": f"-{sun * 0.36:.0f}px",
            "right": f"-{sun * 0.3:.0f}px",
            "width": f"{sun}px",
            "height": f"{sun}px",
            "backgroundImage": url(sun_svg(sun)),
            "opacity": "0.6",
            "willChange": "transform",
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
        # Nergiz and red tulips in the bottom corners, swaying in the spring wind.
        FLOWERS_LEFT: {
            **flowers,
            "left": "72px",
            "backgroundImage": url(flowers_svg(SEED + 3)),
            "animation": "dagwickSway 6s ease-in-out infinite alternate",
        },
        FLOWERS_RIGHT: {
            **flowers,
            "right": "8px",
            "backgroundImage": url(flowers_svg(SEED + 4)),
            "animation": "dagwickSway 7s ease-in-out -3s infinite alternate",
        },
        "@keyframes dagwickSway": {
            "from": {"transform": "rotate(-1.5deg)"},
            "to": {"transform": "rotate(1.5deg)"},
        },
        # Firelight on the hillsides, breathing.
        "body::after": {
            **band,
            "backgroundImage": url(glow_svg()),
            "willChange": "opacity",
            "animation": "dagwickGlow 2.4s ease-in-out infinite alternate",
        },
        "@keyframes dagwickGlow": {"from": {"opacity": "0.55"}, "to": {"opacity": "1"}},
        # The flames: a few still frames shown in turn, so they flicker.
        "html::after": {
            **band,
            "backgroundImage": url(flames_svg()),
            "backgroundSize": f"{W * FLAME_FRAMES}px {H}px",
            "animation": f"dagwickFlames 0.64s steps({FLAME_FRAMES}) infinite",
        },
        "@keyframes dagwickFlames": {
            "from": {"backgroundPosition": "0 bottom"},
            "to": {"backgroundPosition": f"-{W * FLAME_FRAMES}px bottom"},
        },
        # Keep Airflow's sidebar (and its user menu) above the decorations. Airflow's own
        # style for the sidebar outranks theme styles, hence !important.
        '[data-testid="nav-sidebar"]': {"zIndex": f"{SIDEBAR} !important"},
        "@media (prefers-reduced-motion: reduce)": {host: {"animation": "none"} for host in MOVING},
    }
