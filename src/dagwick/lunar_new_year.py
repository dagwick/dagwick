"""Lunar New Year for the whole Airflow UI, drawn with CSS and SVG only (used by the
Lunar New Year theme, which runs from New Year's Eve to the Lantern Festival on the
15th day).

The season ends on the first full moon of the lunar year, so a full moon hangs in the
top-right corner with a thin cloud across it, under a sky of faint stars where a
shooting star streaks past now and then. A string of red palace lanterns sways along
the top of the window: each has gold caps, a warm light inside and a red tassel.
Paper sky lanterns, glowing from their open bases, drift up from the bottom in two
depths, the near ones larger and faster, and float away off the top. Branches of plum
blossom, the flower of the first month, reach in from the bottom corners and stir in
the night air.

Everything is drawn behind Airflow's page and ignores the mouse, so it never covers
Airflow's text, buttons, menus or sidebar; the cards stay clean. The images are still
and CSS transforms move them, so the browser never redraws them while they move.
Viewers who prefer reduced motion get a still scene without shooting stars.
"""

from __future__ import annotations

import math
import random
from typing import Any

from dagwick.scene import settle, url

SEED = 15  # the 15th day of the first month

# Behind Airflow's page: the scene shows in the space Airflow leaves empty.
BEHIND = "-1"

STRING_W, STRING_H = 960, 150  # px; one repeat of the string of lanterns
SKY_W, SKY_H = 1100, 760  # px; one repeat of the rising sky lanterns
NIGHT_W, NIGHT_H = 1400, 400  # px; one repeat of the stars
BLOSSOM_W, BLOSSOM_H = 250, 210  # px; one plum branch in a corner
PLUM_LEFT, PLUM_RIGHT = 23, 19  # seeds of the two plum branches, picked by eye

GOLD = "#e9b949"
BRANCH = "#3a2420"

LANTERN_DEFS = (
    # The red paper body, lit from inside; the gold caps; the light and the glow.
    "<radialGradient id='rb' cx='.45' cy='.45' r='.65'><stop offset='0' stop-color='#ffd59a'/>"
    "<stop offset='.3' stop-color='#f8613a'/><stop offset='.75' stop-color='#d61f1f'/>"
    "<stop offset='1' stop-color='#7f1414'/></radialGradient>"
    "<linearGradient id='gc' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#8a6212'/>"
    "<stop offset='.45' stop-color='#f2c94c'/><stop offset='1' stop-color='#8a6212'/>"
    "</linearGradient>"
    "<radialGradient id='hg'><stop offset='0' stop-color='#ff9a4d' stop-opacity='.5'/>"
    "<stop offset='1' stop-color='#ff7a2e' stop-opacity='0'/></radialGradient>"
    "<radialGradient id='lc'><stop offset='0' stop-color='#fff3c4' stop-opacity='.95'/>"
    "<stop offset='.5' stop-color='#ffc46b' stop-opacity='.45'/>"
    "<stop offset='1' stop-color='#ff8a3d' stop-opacity='0'/></radialGradient>"
    # A round palace lantern hanging from (0, 0); its tassel hangs from (0, 25.2).
    "<g id='ln'><ellipse cy='14' rx='24' ry='22' fill='url(#hg)'/>"
    "<path d='M0 0 V3' stroke='#3b2a1a' stroke-width='.8'/>"
    "<path d='M-4.8 3 H4.8 L3.8 5.6 H-3.8Z' fill='url(#gc)'/>"
    "<ellipse cy='14' rx='10.5' ry='9.6' fill='url(#rb)'/>"
    + "".join(
        f"<ellipse cy='14' rx='{rx}' ry='9.6' fill='none' stroke='#7f1414' "
        "stroke-width='.45' opacity='.55'/>"
        for rx in (3.4, 7)
    )
    + "<path d='M-10.4 14 H10.4' stroke='#7f1414' stroke-width='.35' opacity='.35'/>"
    "<path d='M-3.8 22.6 H3.8 L4.8 25.2 H-4.8Z' fill='url(#gc)'/>"
    "<ellipse cx='-4.2' cy='9.4' rx='3' ry='1.8' fill='#fff' opacity='.13'/></g>"
    # A tall lantern hanging from (0, 0); its tassel hangs from (0, 31).
    "<g id='lt'><ellipse cy='17' rx='20' ry='26' fill='url(#hg)'/>"
    "<path d='M0 0 V3' stroke='#3b2a1a' stroke-width='.8'/>"
    "<path d='M-3.8 3 H3.8 L3 5.4 H-3Z' fill='url(#gc)'/>"
    "<ellipse cy='17' rx='7.4' ry='12.4' fill='url(#rb)'/>"
    + "".join(
        f"<ellipse cy='17' rx='{rx}' ry='12.4' fill='none' stroke='#7f1414' "
        "stroke-width='.45' opacity='.55'/>"
        for rx in (2.4, 5)
    )
    + "<path d='M-3 28.6 H3 L3.8 31 H-3.8Z' fill='url(#gc)'/>"
    "<ellipse cx='-3' cy='11' rx='2' ry='2.6' fill='#fff' opacity='.13'/></g>"
    # A gold knot and red silk tassel hanging from (0, 0).
    "<g id='ts'><path d='M0 0 V2' stroke='#d4a017' stroke-width='.8'/>"
    f"<circle cy='3' r='1.3' fill='{GOLD}'/>"
    "<path d='M-1.6 4 Q-2 9.5 -1.2 12.5 M0 4 V13.5 M1.6 4 Q2 9.5 1.2 12.5' "
    "stroke='#c81e1e' stroke-width='.9' fill='none' stroke-linecap='round'/></g>"
)

SKY_DEFS = (
    # Paper lit by the flame at its base: brightest low in the middle, deeper orange at
    # the rounded top and the edges.
    "<radialGradient id='sk' cx='.5' cy='.85' r='.85'><stop offset='0' stop-color='#fff4c2'/>"
    "<stop offset='.35' stop-color='#ffd27a'/><stop offset='.75' stop-color='#ff9a3c'/>"
    "<stop offset='1' stop-color='#e8621f'/></radialGradient>"
    "<radialGradient id='sh'><stop offset='0' stop-color='#ffb24d' stop-opacity='.6'/>"
    "<stop offset='.4' stop-color='#ff9a3c' stop-opacity='.22'/>"
    "<stop offset='1' stop-color='#ff8a3d' stop-opacity='0'/></radialGradient>"
    # A paper sky lantern: taller than wide, a rounded top, an open base with its flame.
    "<g id='sl'><circle cy='-3' r='24' fill='url(#sh)'/>"
    "<path d='M-5.4 6 C-6.6 -2 -6.8 -9.5 -4.2 -13 Q0 -16 4.2 -13 C6.8 -9.5 6.6 -2 5.4 6 "
    "Q0 7.4 -5.4 6Z' fill='url(#sk)'/>"
    "<path d='M-1.8 -14.6 Q-2.6 -4 -1.9 6.6 M1.8 -14.6 Q2.6 -4 1.9 6.6' fill='none' "
    "stroke='#d9601c' stroke-width='.35' opacity='.4'/>"
    "<ellipse cy='6.2' rx='4.6' ry='1.1' fill='#a8410f' opacity='.6'/>"
    "<ellipse cy='4.4' rx='1.3' ry='1.9' fill='#fff'/></g>"
)


def string_svg() -> str:
    """One repeat of a cord sagging along the top of the window with red lanterns
    hanging from it at different lengths, each lit from inside, with a gold knot and a
    red tassel below (still: CSS sways the string in the breeze)."""
    rng = random.Random(SEED)
    sag = 26
    span = STRING_W / 2  # the cord hangs in two swags per repeat
    cord_y = lambda x: 6 + sag * (1 - math.cos(2 * math.pi * (x % span) / span)) / 2  # noqa: E731
    cord = "M" + " L".join(f"{x:.0f} {cord_y(x):.1f}" for x in range(0, STRING_W + 1, 20))
    lanterns = []
    count = 7
    for i in range(count):
        x = (i + 0.5) * STRING_W / count + rng.uniform(-30, 30)
        top = cord_y(x)
        drop = rng.uniform(4, 34)
        tall = rng.random() < 0.3
        kind, tassel_y, core = ("lt", 31, (17, 5.4, 9)) if tall else ("ln", 25.2, (14, 7.5, 7))
        s = rng.uniform(1.05, 1.45)
        for _ in range(4):  # draws once used for each lantern's own sway: keeps the layout
            rng.random()
        cy, rx, ry = core
        lanterns.append(
            f"<g transform='translate({x:.0f} {top:.1f})'>"
            f"<path d='M0 0 V{drop:.0f}' stroke='#3b2a1a' stroke-width='.7'/>"
            f"<g transform='translate(0 {drop:.0f}) scale({s:.2f})'><use href='#{kind}'/>"
            f"<ellipse cy='{cy}' rx='{rx}' ry='{ry}' fill='url(#lc)' opacity='.75'/>"
            f"<use href='#ts' y='{tassel_y}'/></g><circle r='1.6' fill='{GOLD}'/></g>"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{STRING_W}' height='{STRING_H}'>"
        f"<defs>{LANTERN_DEFS}</defs>"
        f"<path d='{cord}' fill='none' stroke='#3b2a1a' stroke-width='1.1' opacity='.8'/>"
        f"{''.join(lanterns)}</svg>"
    )


def sky_svg(near: bool) -> str:
    """One tile of paper sky lanterns (still: CSS moves the tiles up). The far tile has
    small, dim lanterns; the near tile larger, brighter ones, and rises faster."""
    rng = random.Random(SEED + 1)
    far = [
        (rng.uniform(20, SKY_W - 20), rng.uniform(0, SKY_H), rng.uniform(0.45, 0.75))
        for _ in range(12)
    ]
    close = [
        (rng.uniform(30, SKY_W - 30), rng.uniform(0, SKY_H), rng.uniform(1.1, 2.0))
        for _ in range(7)
    ]
    lanterns = "".join(
        f"<use href='#sl' transform='translate({x:.0f} {y:.0f}) scale({s:.2f})' "
        f"opacity='{0.7 + 0.3 * (s - 1.1) / 0.9 if near else 0.25 + 0.3 * (s - 0.45):.2f}'/>"
        for x, y, s in (close if near else far)
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{SKY_W}' height='{SKY_H}'>"
        f"<defs>{SKY_DEFS}</defs>{lanterns}</svg>"
    )


def night_svg() -> str:
    """One repeat of the night along the top: faint stars in three brightnesses,
    fainter lower down (still; the shooting stars are drawn with CSS)."""
    rng = random.Random(SEED + 2)
    levels: list[list[str]] = [[], [], []]
    for _ in range(46):
        x, y = rng.uniform(0, NIGHT_W), rng.uniform(4, NIGHT_H * 0.7)
        fade = 1 - y / (NIGHT_H * 0.75)
        levels[min(2, int(fade * 3))].append(f"M{x:.0f} {y:.0f}h0")
    stars = "".join(
        f"<path d='{''.join(dots)}' stroke-width='{1.4 + i * 0.5:.1f}' "
        f"opacity='{0.3 + i * 0.25:.2f}'/>"
        for i, dots in enumerate(levels)
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{NIGHT_W}' height='{NIGHT_H}'>"
        f"<g stroke='#fff6dc' stroke-linecap='round'>{stars}</g></svg>"
    )


def moon_svg(size: int) -> str:
    """The first full moon of the year: warm, with soft grey-gold shadows, a halo and
    a thin cloud across it."""
    c = size / 2
    r = size * 0.2
    shadows = "".join(
        f"<ellipse cx='{c + dx * r:.1f}' cy='{c + dy * r:.1f}' rx='{rx * r:.1f}' "
        f"ry='{ry * r:.1f}' fill='#cfae68' opacity='.32'/>"
        for dx, dy, rx, ry in (
            (-0.3, -0.25, 0.35, 0.25),
            (0.25, 0.1, 0.3, 0.38),
            (-0.1, 0.45, 0.25, 0.15),
        )
    )
    cloud = (
        f"<g transform='translate({c - r * 0.3:.0f} {c + r * 0.35:.0f})' filter='url(#cb)' "
        "fill='#7d6f8f' opacity='.45'>"
        f"<ellipse rx='{r * 1.5:.0f}' ry='{r * 0.13:.1f}'/>"
        f"<ellipse cx='{r * 0.4:.0f}' cy='{-r * 0.14:.1f}' rx='{r * 0.8:.0f}' ry='{r * 0.12:.1f}'/>"
        "</g>"
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>"
        "<defs><radialGradient id='h'><stop offset='.2' stop-color='#ffe7a8' stop-opacity='.4'/>"
        "<stop offset='1' stop-color='#ffd27a' stop-opacity='0'/></radialGradient>"
        "<radialGradient id='d' cx='.42' cy='.4'><stop offset='0' stop-color='#fff8e1'/>"
        "<stop offset='1' stop-color='#f3d189'/></radialGradient>"
        "<filter id='b'><feGaussianBlur stdDeviation='3'/></filter>"
        "<filter id='cb' x='-50%' y='-200%' width='200%' height='500%'>"
        "<feGaussianBlur stdDeviation='2.5'/></filter>"
        f"<clipPath id='c'><circle cx='{c}' cy='{c}' r='{r:.1f}'/></clipPath></defs>"
        f"<circle cx='{c}' cy='{c}' r='{c}' fill='url(#h)'/>"
        f"<circle cx='{c}' cy='{c}' r='{r:.1f}' fill='url(#d)'/>"
        f"<g clip-path='url(#c)'><g filter='url(#b)'>{shadows}</g></g>{cloud}</svg>"
    )


BLOSSOMS = {
    # key: (heart, edge) of the petals: pale pink, white and deep rose
    "fp": ("#fff1f5", "#f48fb1"),
    "fw": ("#ffffff", "#fbd3df"),
    "fr": ("#ffd6e2", "#e0457b"),
}
STAMENS = [2 * math.pi * k / 7 + 0.3 for k in range(7)]
BLOSSOM_DEFS = "".join(
    f"<radialGradient id='g{key}'><stop offset='0' stop-color='{heart}'/>"
    f"<stop offset='1' stop-color='{edge}'/></radialGradient>"
    for key, (heart, edge) in BLOSSOMS.items()
) + "".join(
    # A plum blossom facing us: five round petals, a deep red heart and gold stamens.
    f"<g id='{key}'>"
    + "".join(
        f"<circle cy='-2.7' r='2.8' fill='url(#g{key})' transform='rotate({k * 72})'/>"
        for k in range(5)
    )
    + "<circle r='1.25' fill='#b3123f'/><path d='"
    + "".join(f"M0 0L{2.6 * math.cos(a):.1f} {2.6 * math.sin(a):.1f}" for a in STAMENS)
    + "' stroke='#f6c453' stroke-width='.3'/><path d='"
    + "".join(f"M{2.6 * math.cos(a):.1f} {2.6 * math.sin(a):.1f}h0" for a in STAMENS)
    + "' stroke='#f6c453' stroke-width='.8' stroke-linecap='round'/></g>"
    for key in BLOSSOMS
)


Point = tuple[float, float]
Branch = tuple[list[tuple[str, float]], list[tuple[float, float, float, str]], list[Point]]


def _plum(seed: int, side: int) -> Branch:
    """A crooked plum branch reaching in from a bottom corner (``side`` 1: the left
    corner, leaning right; -1: the right corner, leaning left): its wood as (path,
    width), its blossoms as (x, y, size, kind) and its buds. The wood turns at sharp
    elbows and splits into twigs; blossoms sit straight on it in small clusters and red
    buds tip the twigs."""
    rng = random.Random(seed)
    W, H = BLOSSOM_W, BLOSSOM_H
    wood: list[tuple[str, float]] = []
    flowers: list[tuple[float, float, float, str]] = []
    buds: list[tuple[float, float]] = []

    def bloom(x: float, y: float, size: float) -> None:
        kind = rng.choices(tuple(BLOSSOMS), (0.45, 0.3, 0.25))[0]
        flowers.append((x, y, size, kind))

    def grow(x: float, y: float, angle: float, length: float, width: float, segs: int) -> None:
        for step in range(segs):
            angle += rng.choice((-1, 1)) * rng.uniform(12, 30)  # plum wood turns sharply
            angle = max(15.0, min(82.0, angle))  # upwards and into the page
            seg = length * rng.uniform(0.75, 1.15)
            nx = min(W - 10.0, max(10.0, x + side * seg * math.sin(math.radians(angle))))
            ny = max(18.0, y - seg * math.cos(math.radians(angle)))
            wood.append((f"M{x:.1f} {y:.1f}L{nx:.1f} {ny:.1f}", width))
            if width < 5:
                for _ in range(rng.choice((0, 1, 1, 2))):
                    t = rng.uniform(0.25, 1)
                    bloom(
                        x + (nx - x) * t + rng.uniform(-2.5, 2.5),
                        y + (ny - y) * t + rng.uniform(-2.5, 2.5),
                        rng.uniform(1.0, 1.5),
                    )
            if segs - step > 1 and width > 1.6 and rng.random() < 0.65:
                twig = angle + rng.choice((-1, 1)) * rng.uniform(35, 55)
                grow(nx, ny, twig, length * 0.62, width * 0.55, max(2, segs - step - 2))
            x, y, width = nx, ny, max(1.0, width * 0.74)
        buds.append((x, y))
        bloom(x - side * 1.5, y + 4, rng.uniform(0.9, 1.2))

    grow(side == 1 and 12 or W - 12, H + 4, 40, 36, 8, 6)
    return wood, flowers, buds


def blossom_svg(seed: int, side: int) -> str:
    """A plum branch in blossom for a bottom corner (still: CSS makes it sway)."""
    wood, flowers, buds = _plum(seed, side)
    rng = random.Random(seed + 1)
    branch = "".join(
        f"<path d='{d}' stroke-width='{w:.1f}'/>" for d, w in wood
    ) + "".join(  # a lit edge along the wood, so it shows on a dark page
        f"<path d='{d}' stroke='#8a5a44' stroke-width='{w * 0.3:.1f}' "
        f"transform='translate({-side * w * 0.2:.1f} 0)' opacity='.7'/>"
        for d, w in wood
        if w > 1.4
    )
    blooms = []
    for fx, fy, s, kind in flowers:
        squash = rng.choice((1, 1, 0.8, 0.65))
        blooms.append(
            f"<use href='#{kind}' transform='translate({fx:.1f} {fy:.1f}) "
            f"rotate({rng.uniform(0, 72):.0f}) scale({s:.2f} {s * squash:.2f})'/>"
        )
    blooms.append(
        "<path d='"
        + "".join(f"M{bx:.1f} {by:.1f}h0" for bx, by in buds)
        + "' stroke='#c2264f' stroke-width='4.2' stroke-linecap='round'/>"
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{BLOSSOM_W}' height='{BLOSSOM_H}'>"
        f"<defs>{BLOSSOM_DEFS}</defs>"
        f"<g fill='none' stroke='{BRANCH}' stroke-linecap='round' stroke-linejoin='round'>"
        f"{branch}</g>{''.join(blooms)}</svg>"
    )


NIGHT_HOST = "html::before"
SKY_HOST = "body::before"
FAR_HOST = "body::after"
MOON_HOST = "#root::before"
SHOOTING_HOST = "#root::after"
STRING_HOST = "html::after"
BLOSSOM_LEFT = '[data-testid="main-content"]::before'
BLOSSOM_RIGHT = '[data-testid="main-content"]::after'
HOSTS = (
    NIGHT_HOST,
    SKY_HOST,
    FAR_HOST,
    MOON_HOST,
    SHOOTING_HOST,
    STRING_HOST,
    BLOSSOM_LEFT,
    BLOSSOM_RIGHT,
)
MOVING = (SKY_HOST, FAR_HOST, SHOOTING_HOST, STRING_HOST, BLOSSOM_LEFT, BLOSSOM_RIGHT)

# Shooting stars, one at a time: (where it starts across the window, px from the top,
# heading in degrees, when in the cycle it falls as a percentage).
SHOOTING = ((62, 40, 24, 0), (18, 110, 16, 33), (82, 150, 152, 66))


def shooting_keyframes() -> dict[str, dict[str, str]]:
    """One streak crossing the sky three times a cycle, each time somewhere else, and
    invisible in between."""
    frames: dict[str, dict[str, str]] = {}
    for x, y, heading, at in SHOOTING:
        start = f"translate({x}vw, {y}px) rotate({heading}deg) translateX(0)"
        end = f"translate({x}vw, {y}px) rotate({heading}deg) translateX(280px)"
        frames[f"{at}%"] = {"opacity": "0", "transform": start}
        frames[f"{at + 0.6:g}%"] = {"opacity": "1"}
        frames[f"{at + 4:g}%"] = {"opacity": "1"}
        frames[f"{at + 5.5:g}%"] = {"opacity": "0", "transform": end}
    frames["100%"] = frames["0%"]
    return frames


# A warm glow along the bottom, where the sky lanterns are lit.
GLOW = "radial-gradient(ellipse 70% 220px at 50% 100%, rgba(251, 146, 60, 0.13), transparent 70%)"


def global_css() -> dict[str, Any]:
    """Lunar New Year as Airflow theme ``globalCss`` (selector -> style).

    Every image is still: CSS moves the layers with transforms, which the browser does
    without redrawing them, so the theme costs Airflow almost nothing.
    """
    layer = {"content": '""', "position": "fixed", "pointerEvents": "none", "zIndex": BEHIND}
    band = {**layer, "left": "0", "right": "0", "backgroundRepeat": "repeat-x"}
    moon = 230
    plum = f"{BLOSSOM_W}px {BLOSSOM_H}px"
    blossom = {
        **layer,
        "bottom": "0",
        "width": f"{BLOSSOM_W}px",
        "height": f"{BLOSSOM_H}px",
        "backgroundSize": plum,
    }
    rising = {
        **layer,
        "left": "0",
        "right": "0",
        "top": "0",
        "height": f"calc(100vh + {SKY_H}px)",
        "backgroundSize": f"{SKY_W}px {SKY_H}px",
        "backgroundPosition": "center 0",
    }
    css: dict[str, Any] = {
        # Faint stars across the top and a warm glow along the bottom, where the sky
        # lanterns are lit (painted first, under everything else).
        NIGHT_HOST: {
            **layer,
            "inset": "0",
            "backgroundImage": f"{url(night_svg())}, {GLOW}",
            "backgroundRepeat": "repeat-x, no-repeat",
            "backgroundPosition": "center top, center bottom",
            "backgroundSize": f"{NIGHT_W}px {NIGHT_H}px, 100% 100%",
        },
        # No stars on a light page, only the glow.
        "html.light::before": {"backgroundImage": GLOW, "backgroundSize": "100% 100%"},
        # Sky lanterns rising from the bottom and up off the top of the window, in two
        # depths: the near ones climb twice as fast as the far ones. Each layer is one
        # tile taller than the window and slides up by a tile, so the browser only
        # moves it, never redraws it.
        SKY_HOST: {
            **rising,
            "backgroundImage": url(sky_svg(near=True)),
            "animation": "dagwickLanterns 66s linear infinite",
        },
        FAR_HOST: {
            **rising,
            "backgroundImage": url(sky_svg(near=False)),
            "animation": "dagwickLanterns 132s linear infinite",
        },
        "@keyframes dagwickLanterns": {
            "from": {"transform": "translateY(0)"},
            "to": {"transform": f"translateY(-{SKY_H}px)"},
        },
        # The full moon in the corner.
        MOON_HOST: {
            **layer,
            "top": f"-{moon * 0.27:.0f}px",
            "right": f"-{moon * 0.2:.0f}px",
            "width": f"{moon}px",
            "height": f"{moon}px",
            "backgroundImage": url(moon_svg(moon)),
            "opacity": "0.8",
        },
        "html.light #root::before": {"opacity": "0.95"},
        # A shooting star now and then: a short streak, bright at its head.
        SHOOTING_HOST: {
            **layer,
            "top": "0",
            "left": "0",
            "width": "110px",
            "height": "2px",
            "borderRadius": "1px",
            "backgroundImage": "linear-gradient(to right, transparent, "
            "rgba(255, 215, 106, 0.5) 65%, #fffbe8)",
            "opacity": "0",
            "animation": "dagwickShooting 18s linear infinite",
        },
        "html.light #root::after": {
            "backgroundImage": "linear-gradient(to right, transparent, "
            "rgba(217, 154, 6, 0.6) 65%, #d99a06)",
        },
        "@keyframes dagwickShooting": shooting_keyframes(),
        # Plum blossom in the bottom corners, stirring in the night air.
        BLOSSOM_LEFT: {
            **blossom,
            "left": "64px",
            "transformOrigin": "0 100%",
            "backgroundImage": url(blossom_svg(PLUM_LEFT, 1)),
            "animation": "dagwickPlum 14s ease-in-out infinite",
        },
        BLOSSOM_RIGHT: {
            **blossom,
            "right": "0",
            "transformOrigin": "100% 100%",
            "backgroundImage": url(blossom_svg(PLUM_RIGHT, -1)),
            "animation": "dagwickPlum 16s ease-in-out -8s infinite",
        },
        "@keyframes dagwickPlum": {
            "25%": {"transform": "rotate(-1deg)"},
            "75%": {"transform": "rotate(1deg)"},
        },
        # The string of red lanterns along the top, swaying in the breeze: a slant from
        # the top, so the lanterns swing while the cord stays where it hangs.
        STRING_HOST: {
            **band,
            "top": "0",
            "height": f"{STRING_H}px",
            "backgroundImage": url(string_svg()),
            "backgroundPosition": "center top",
            "backgroundSize": f"{STRING_W}px {STRING_H}px",
            "transformOrigin": "50% 0",
            "animation": "dagwickBreeze 10s ease-in-out infinite",
        },
        "@keyframes dagwickBreeze": {
            "25%": {"transform": "skewX(-3deg)"},
            "75%": {"transform": "skewX(3deg)"},
        },
        "@media (prefers-reduced-motion: reduce)": {host: {"animation": "none"} for host in MOVING},
    }
    return settle(css)
