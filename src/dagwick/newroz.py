"""Newroz for the whole Airflow UI, drawn with CSS only (used by the Newroz theme).

Dawn breaks behind three ranges of mountains along the bottom of the window, the
nearer ones darker and the farther ones lost in haze. Bonfires burn on four peaks:
their flames flicker, their light breathes on the hillsides and sparks rise from
them. The Kurdish sun, with its 21 rays, turns slowly in the top-right corner.

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
COLOURS = {
    # range: (top, bottom) of its fill, dark then light Airflow
    "dark": {
        "far": ("#3c6e74", "#25494f"),
        "mid": ("#21573f", "#173d2c"),
        "near": ("#123a24", "#0b2416"),
    },
    "light": {
        "far": ("#d8ece6", "#c3e0d6"),
        "mid": ("#a9d9ba", "#8dcaa3"),
        "near": ("#6fb98a", "#4fa26f"),
    },
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


def smooth_path(pts: list[Point]) -> str:
    """A closed shape under a smooth line through the points (Catmull-Rom as Béziers)."""
    out = [f"M0 {H} L{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    ext = [(pts[-2][0] - W, pts[-2][1]), *pts, (pts[1][0] + W, pts[1][1])]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(out) + f" L{W} {H}Z"


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
    """One repeat of the three ranges, each with a soft gradient, and the fires' logs."""
    ridges, fires = ranges()
    defs, shapes = [], []
    for name, *_ in RANGES:
        top, bottom = COLOURS[theme][name]
        defs.append(
            f"<linearGradient id='{name}' x1='0' y1='0' x2='0' y2='1'>"
            f"<stop offset='0' stop-color='{top}'/><stop offset='1' stop-color='{bottom}'/>"
            "</linearGradient>"
        )
        shapes.append(f"<path d='{smooth_path(ridges[name])}' fill='url(#{name})'/>")
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


MOVING = ("html::before", "html::after", "body::after", "#root::before")


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
            "height": "240px",
            "backgroundImage": "radial-gradient(ellipse 70% 100% at 50% 100%, "
            "rgba(251, 146, 60, 0.16), transparent 70%), "
            "linear-gradient(to top, rgba(22, 163, 74, 0.10), transparent)",
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
        "#root::after": {**band, "backgroundImage": url(mountains_svg("dark")), "opacity": "0.8"},
        "html.light #root::after": {
            "backgroundImage": url(mountains_svg("light")),
            "opacity": "0.75",
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
