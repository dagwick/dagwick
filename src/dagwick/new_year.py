"""New Year for the whole Airflow UI, drawn with CSS only (used by the New Year theme).

A calm midnight sky behind Airflow: a few soft fireworks bloom and fade slowly, each
on its own rhythm, gold stars twinkle, and a warm glow rises from the bottom of the
window. Everything is drawn *behind* Airflow's page, so it only shows in the space
around the cards and never covers text, buttons or menus. It moves with CSS
transforms and opacity, which the graphics card does without repainting the page.
Viewers who prefer reduced motion get a still scene.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from dagwick.snow import url

SEED = 1231
BEHIND = "-1"  # below Airflow's page content, above the window's background

STAR = ("#fde68a", "#fef3c7", "#fcd34d")


@dataclass(frozen=True)
class Kind:
    """One kind of firework: its colours, how many streaks, how much they bend down."""

    name: str
    mid: str  # colour along the streak
    tip: str  # the bright end of the streak
    glitter: str
    rays: int
    droop: float  # how far the streaks bend down, as a share of the radius


KINDS = (
    Kind("willow", "#f59e0b", "#fef3c7", "#fcd34d", 34, 0.32),  # gold, long and drooping
    Kind("peony", "#e11d48", "#fecdd3", "#fda4af", 28, 0.12),  # crimson, round
    Kind("chrysanthemum", "#60a5fa", "#f8fafc", "#e0f2fe", 30, 0.18),  # silver-blue
)


def _move(x: float, y: float, scale: float = 1.0) -> str:
    return f"translate3d({x:.0f}px, {y:.0f}px, 0) scale({scale:.2f})"


# ---- fireworks ----

# Page-level pseudo-elements, free on every Airflow page. Not the sidebar's: anything
# drawn there would sit in the sidebar's layer, above the page.
BURST_HOSTS = ("html::after", "body::after", "#root::before", "#root::after")


@dataclass(frozen=True)
class Burst:
    size: int  # px
    left: float  # vw, where the centre is
    top: float  # vh
    kind: Kind
    seed: int
    seconds: float
    delay: float  # negative: the cycle has already started when the page opens


def burst_svg(burst: Burst) -> str:
    """One firework: curved streaks that brighten towards their tips, bending down as
    if pulled by gravity, with a soft glow and glitter falling off the ends.

    One radial gradient colours every streak by its distance from the centre: dark at
    the centre, the firework's colour along the way, near white at the tip.
    """
    rng = random.Random(burst.seed)
    kind = burst.kind
    r = burst.size / 2
    streaks, glitter = [], []
    for i in range(kind.rays):
        a = math.tau * i / kind.rays + rng.uniform(-0.06, 0.06)
        # Shorter when they droop, so the bent ends stay inside the drawing.
        reach = r * rng.uniform(0.78, 0.92) / (1 + kind.droop * 1.1)
        start = r * 0.1
        dx, dy = math.cos(a), math.sin(a)
        # Gravity: the far half of each streak bends down.
        x1, y1 = dx * reach, dy * reach + kind.droop * r * (0.6 + 0.4 * abs(dx))
        cx, cy = dx * reach * 0.62, dy * reach * 0.62 + kind.droop * r * 0.12
        streaks.append(f"M{dx * start:.1f} {dy * start:.1f} Q{cx:.1f} {cy:.1f} {x1:.1f} {y1:.1f}")
        for k in range(rng.randint(1, 3)):  # glitter drifting below the tip
            gx = x1 + rng.uniform(-2, 2)
            gy = y1 + 4 + k * rng.uniform(4, 7)
            glitter.append(
                f"<circle cx='{gx:.1f}' cy='{gy:.1f}' r='{rng.uniform(0.6, 1.2):.1f}' "
                f"fill='{kind.glitter}' opacity='{0.75 - k * 0.2:.2f}'/>"
            )
    d = " ".join(streaks)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{burst.size}' height='{burst.size}' "
        f"viewBox='{-r:.0f} {-r:.0f} {burst.size} {burst.size}'>"
        "<defs>"
        f"<radialGradient id='s' gradientUnits='userSpaceOnUse' cx='0' cy='0' r='{r:.0f}'>"
        f"<stop offset='0' stop-color='{kind.mid}' stop-opacity='0'/>"
        f"<stop offset='.35' stop-color='{kind.mid}' stop-opacity='.55'/>"
        f"<stop offset='.8' stop-color='{kind.tip}' stop-opacity='.95'/>"
        f"<stop offset='1' stop-color='{kind.tip}' stop-opacity='.2'/>"
        "</radialGradient>"
        "<filter id='b' x='-20%' y='-20%' width='140%' height='140%'>"
        "<feGaussianBlur stdDeviation='2.6'/></filter>"
        "<radialGradient id='c'>"
        f"<stop offset='0' stop-color='{kind.tip}' stop-opacity='.9'/>"
        f"<stop offset='.35' stop-color='{kind.mid}' stop-opacity='.45'/>"
        f"<stop offset='1' stop-color='{kind.mid}' stop-opacity='0'/>"
        "</radialGradient>"
        "</defs>"
        f"<circle r='{r * 0.12:.0f}' fill='url(#c)'/>"
        f"<path d='{d}' fill='none' stroke='url(#s)' stroke-width='3.4' "
        "stroke-linecap='round' filter='url(#b)' opacity='.7'/>"
        f"<path d='{d}' fill='none' stroke='url(#s)' stroke-width='1.3' stroke-linecap='round'/>"
        f"{''.join(glitter)}"
        "</svg>"
    )


def bursts(rng: random.Random) -> list[Burst]:
    """Four fireworks spread over the window, clear of the sidebar; gold leads."""
    spots = [(22, 18), (46, 30), (68, 14), (87, 32)]
    kinds = [KINDS[0], KINDS[1], KINDS[0], KINDS[2]]
    out = []
    for i, ((left, top), kind) in enumerate(zip(spots, kinds, strict=True)):
        out.append(
            Burst(
                size=rng.choice((280, 320, 360)),
                left=left + rng.uniform(-3, 3),
                top=top + rng.uniform(-4, 4),
                kind=kind,
                seed=rng.randint(0, 10_000),
                seconds=round(rng.uniform(9, 12), 1),
                delay=-round(i * 2.6 + rng.uniform(0, 1), 1),
            )
        )
    return out


def fireworks(rng: random.Random) -> dict[str, Any]:
    """Each firework blooms slowly, drifts down a little and fades, then rests."""
    css: dict[str, Any] = {
        ", ".join(BURST_HOSTS): {
            "content": '""',
            "position": "fixed",
            "pointerEvents": "none",
            "zIndex": BEHIND,
            "opacity": "0",
            "backgroundRepeat": "no-repeat",
            "backgroundSize": "100% 100%",
            "willChange": "transform, opacity",
        }
    }
    for i, (host, b) in enumerate(zip(BURST_HOSTS, bursts(rng), strict=True)):
        name = f"dagwickFirework{i}"
        css[host] = {
            "width": f"{b.size}px",
            "height": f"{b.size}px",
            "left": f"calc({b.left:.1f}vw - {b.size // 2}px)",
            "top": f"calc({b.top:.1f}vh - {b.size // 2}px)",
            "backgroundImage": url(burst_svg(b)),
            "animation": f"{name} {b.seconds}s ease-out {b.delay}s infinite",
        }
        droop = b.size * 0.05
        css[f"@keyframes {name}"] = {
            "0%": {"opacity": "0", "transform": _move(0, 0, 0.2)},
            "6%": {"opacity": "0.9", "transform": _move(0, 0, 0.55)},
            "30%": {"opacity": "0.8", "transform": _move(0, droop / 2, 1)},
            "55%": {"opacity": "0", "transform": _move(0, droop, 1.04)},
            "100%": {"opacity": "0", "transform": _move(0, droop, 1.04)},
        }
    return css


# ---- stars and glow ----


def stars_svg(rng: random.Random, width: int, height: int, count: int) -> str:
    """Small gold stars and glints scattered over one repeat."""
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"]
    for _ in range(count):
        x, y = rng.uniform(0, width), rng.uniform(0, height * 0.7)  # mostly in the sky
        color, op = rng.choice(STAR), rng.uniform(0.35, 0.8)
        if rng.random() < 0.3:
            s = rng.uniform(3, 5)  # a four-pointed glint
            star = (
                f"M{x:.0f} {y - s:.1f} L{x + s / 4:.1f} {y:.0f} L{x:.0f} {y + s:.1f} "
                f"L{x - s / 4:.1f} {y:.0f}Z M{x - s:.1f} {y:.0f} L{x:.0f} {y + s / 4:.1f} "
                f"L{x + s:.1f} {y:.0f} L{x:.0f} {y - s / 4:.1f}Z"
            )
            out.append(f"<path d='{star}' fill='{color}' opacity='{op:.2f}'/>")
        else:
            out.append(
                f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{rng.uniform(0.6, 1.3):.1f}' "
                f"fill='{color}' opacity='{op:.2f}'/>"
            )
    out.append("</svg>")
    return "".join(out)


def global_css() -> dict[str, Any]:
    """New Year as Airflow theme ``globalCss`` (selector -> style)."""
    rng = random.Random(SEED)
    star_w, star_h = 1180, 760
    return {
        **fireworks(rng),
        # Gold stars that slowly brighten and dim.
        "html::before": {
            "content": '""',
            "position": "fixed",
            "inset": "0",
            "pointerEvents": "none",
            "zIndex": BEHIND,
            "backgroundImage": url(stars_svg(rng, star_w, star_h, 46)),
            "backgroundSize": f"{star_w}px {star_h}px",
            "willChange": "opacity",
            "animation": "dagwickStars 7s ease-in-out infinite alternate",
        },
        "@keyframes dagwickStars": {"from": {"opacity": "0.55"}, "to": {"opacity": "1"}},
        # A warm glow rising from the bottom, and a deeper night at the top.
        "body::before": {
            "content": '""',
            "position": "fixed",
            "inset": "0",
            "pointerEvents": "none",
            "zIndex": BEHIND,
            "backgroundImage": (
                "linear-gradient(to top, rgba(251, 191, 36, 0.14), transparent 160px), "
                "radial-gradient(ellipse at top, rgba(49, 46, 129, 0.35), transparent 60%)"
            ),
        },
        "html.light body::before": {
            "backgroundImage": (
                "linear-gradient(to top, rgba(245, 158, 11, 0.12), transparent 160px), "
                "radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08), transparent 60%)"
            ),
        },
        # Reduced motion: the stars and fireworks stand still.
        "@media (prefers-reduced-motion: reduce)": {
            "html::before": {"animation": "none"},
            ", ".join(BURST_HOSTS): {"animation": "none", "opacity": "0.45", "transform": "none"},
        },
    }
