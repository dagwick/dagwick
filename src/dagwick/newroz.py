"""Newroz for the whole Airflow UI, drawn with CSS only (used by the Newroz theme).

The Kurdish sun rises in the top-right corner, mountains run along the bottom of the
window with bonfires burning on their peaks, the fires glow and flicker, and embers
rise slowly from them. Spring green lights the foot of the page. Everything moves with
CSS transforms or fades, which the graphics card does without repainting the page, and
viewers who prefer reduced motion get a still scene.
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

RIDGE_W, RIDGE_H = 1200, 100  # one repeat of the mountains, in px
# Each ridge is a line of (x, y) points; a fire burns on the peaks listed in FIRES.
FAR = ((0, 65), (90, 48), (170, 62), (280, 34), (390, 58), (470, 45), (560, 64), (680, 38),
       (790, 60), (880, 41), (980, 63), (1090, 46), (1200, 65))  # fmt: skip
NEAR = ((0, 82), (130, 65), (240, 80), (360, 53), (480, 81), (600, 68), (720, 84),
        (850, 58), (980, 82), (1100, 70), (1200, 82))  # fmt: skip
FIRES = ((360, 53), (850, 58), (280, 34), (680, 38))  # two near, two far

EMBER_W, EMBER_H = 1200, 700


def _ridge(points: tuple[tuple[int, int], ...], fill: str) -> str:
    line = " ".join(f"L{x} {y}" for x, y in points)
    return f"<path d='M0 {RIDGE_H} {line} V{RIDGE_H}Z' fill='{fill}'/>"


def _fire(x: int, y: int, scale: float) -> str:
    """A bonfire: a pile of logs and three tongues of flame."""
    s = scale
    flame = (
        f"<path d='M0 0 C{-9 * s:.1f} {-6 * s:.1f} {-6 * s:.1f} {-16 * s:.1f} 0 {-26 * s:.1f} "
        f"C{6 * s:.1f} {-16 * s:.1f} {9 * s:.1f} {-6 * s:.1f} 0 0Z' fill='#f97316'/>"
        f"<path d='M0 0 C{-5 * s:.1f} {-4 * s:.1f} {-4 * s:.1f} {-10 * s:.1f} 0 {-17 * s:.1f} "
        f"C{4 * s:.1f} {-10 * s:.1f} {5 * s:.1f} {-4 * s:.1f} 0 0Z' fill='#facc15'/>"
        f"<path d='M0 0 C{-2 * s:.1f} {-2 * s:.1f} {-2 * s:.1f} {-5 * s:.1f} 0 {-9 * s:.1f} "
        f"C{2 * s:.1f} {-5 * s:.1f} {2 * s:.1f} {-2 * s:.1f} 0 0Z' fill='#fef9c3'/>"
    )
    side = f"<g transform='translate({-7 * s:.1f} {2 * s:.1f}) rotate(-24) scale(.7)'>{flame}</g>"
    other = f"<g transform='translate({7 * s:.1f} {2 * s:.1f}) rotate(22) scale(.6)'>{flame}</g>"
    logs = (
        f"<path d='M{-9 * s:.1f} {3 * s:.1f} L{9 * s:.1f} {-1 * s:.1f} M{-9 * s:.1f} "
        f"{-1 * s:.1f} L{9 * s:.1f} {3 * s:.1f}' stroke='#3f2a1d' stroke-width='{2.4 * s:.1f}' "
        "stroke-linecap='round'/>"
    )
    return f"<g transform='translate({x} {y})'>{side}{other}{flame}{logs}</g>"


def mountains_svg(theme: str) -> str:
    """One repeat of the mountains, with bonfires on four peaks."""
    far, near = {
        "dark": ("#1f4d3c", "#123628"),
        "light": ("#bfe3cc", "#86c7a1"),
    }[theme]
    fires = "".join(_fire(x, y, 0.8 if (x, y) in NEAR else 0.55) for x, y in FIRES)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{RIDGE_W}' height='{RIDGE_H}'>"
        f"{_ridge(FAR, far)}{_ridge(NEAR, near)}{fires}</svg>"
    )


def glow_svg() -> str:
    """The light of the fires on the mountainsides, for the flicker layer."""
    spots = "".join(
        f"<circle cx='{x}' cy='{y - 8}' r='{36 if (x, y) in NEAR else 24}' fill='url(#g)'/>"
        for x, y in FIRES
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{RIDGE_W}' height='{RIDGE_H}'>"
        "<defs><radialGradient id='g'><stop offset='0' stop-color='#fb923c' stop-opacity='.55'/>"
        "<stop offset='1' stop-color='#fb923c' stop-opacity='0'/></radialGradient></defs>"
        f"{spots}</svg>"
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
        "<stop offset='1' stop-color='#fde68a' stop-opacity='0'/></radialGradient></defs>"
        f"<circle cx='{c}' cy='{c}' r='{c}' fill='url(#h)'/>"
        f"<path d='{' '.join(rays)}' fill='{GOLD}'/>"
        f"<circle cx='{c}' cy='{c}' r='{disc:.1f}' fill='{GOLD}'/></svg>"
    )


def embers_svg(rng: random.Random, count: int) -> str:
    """One repeat of rising embers: small, warm, soft dots at random places."""
    dots = []
    for _ in range(count):
        x, y = rng.uniform(0, EMBER_W), rng.uniform(0, EMBER_H)
        r, op = rng.uniform(1.2, 2.4), rng.uniform(0.45, 0.85)
        dots.append(
            f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{r:.1f}' fill='url(#e)' opacity='{op:.2f}'/>"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{EMBER_W}' height='{EMBER_H}'>"
        "<defs><radialGradient id='e'><stop offset='0' stop-color='#fff7d6'/>"
        "<stop offset='.45' stop-color='#fb923c'/>"
        "<stop offset='1' stop-color='#f97316' stop-opacity='0'/></radialGradient></defs>"
        f"{''.join(dots)}</svg>"
    )


def _move(x: float, y: float) -> dict[str, str]:
    return {"transform": f"translate3d({x:.0f}px, {y:.0f}px, 0)"}


MOVING = ("html::before", "html::after")


def global_css() -> dict[str, Any]:
    """Newroz as Airflow theme ``globalCss`` (selector -> style)."""
    rng = random.Random(SEED)
    layer = {"content": '""', "position": "fixed", "pointerEvents": "none", "zIndex": TOP}
    ridge = {
        **layer,
        "left": "0",
        "right": "0",
        "bottom": "0",
        "height": f"{RIDGE_H}px",
        "backgroundSize": f"{RIDGE_W}px {RIDGE_H}px",
        "backgroundRepeat": "repeat-x",
        "backgroundPosition": "center bottom",
    }
    return {
        # Embers rising from the fires, with a gentle sway.
        "html::before": {
            **layer,
            "top": "0",
            "bottom": f"-{EMBER_H}px",
            "left": "-40px",
            "right": "-40px",
            "backgroundImage": url(embers_svg(rng, 14)),
            "backgroundSize": f"{EMBER_W}px {EMBER_H}px",
            "willChange": "transform",
            "animation": "dagwickEmbers 30s linear infinite",
        },
        "@keyframes dagwickEmbers": {
            "0%": _move(0, 0),
            "25%": _move(14, -EMBER_H / 4),
            "50%": _move(0, -EMBER_H / 2),
            "75%": _move(-14, -EMBER_H * 3 / 4),
            "100%": _move(0, -EMBER_H),
        },
        # The firelight on the mountains, flickering (html::after paints after #root::after,
        # so it lies over the mountains at the same z-index).
        "html::after": {
            **ridge,
            "backgroundImage": url(glow_svg()),
            "willChange": "opacity",
            "animation": "dagwickFire 1.8s ease-in-out infinite alternate",
        },
        "@keyframes dagwickFire": {"0%": {"opacity": "0.55"}, "100%": {"opacity": "1"}},
        # The mountains and their bonfires.
        "#root::after": {**ridge, "backgroundImage": url(mountains_svg("dark")), "opacity": "0.7"},
        "html.light #root::after": {"backgroundImage": url(mountains_svg("light"))},
        # The sun in the corner and spring green at the foot of the page.
        "body::before": {
            **layer,
            "inset": "0",
            "backgroundImage": f"{url(sun_svg(200))}, "
            "linear-gradient(to top, rgba(22, 163, 74, 0.16), transparent 220px)",
            "backgroundRepeat": "no-repeat",
            "backgroundPosition": "right -44px top -52px, 0 0",
            "backgroundSize": "150px 150px, 100% 100%",
            "opacity": "0.6",
        },
        "html.light body::before": {"opacity": "0.8"},
        # Keep Airflow's sidebar (and its user menu) above the decorations. Airflow's own
        # style for the sidebar outranks theme styles, hence !important.
        '[data-testid="nav-sidebar"]': {"zIndex": f"{SIDEBAR} !important"},
        "@media (prefers-reduced-motion: reduce)": {host: {"animation": "none"} for host in MOVING},
    }
