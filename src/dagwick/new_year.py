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

# Soft, warm colours: gold first, a few cool accents.
COLORS = ("#fcd34d", "#fbbf24", "#f9a8d4", "#a5b4fc", "#67e8f9")
STAR = ("#fde68a", "#fef3c7", "#fcd34d")


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
    outer: str
    inner: str
    rays: int
    seconds: float
    delay: float  # negative: the cycle has already started when the page opens


def burst_svg(burst: Burst) -> str:
    """One firework: thin rays of sparks fading towards the centre, and a soft glow."""
    r = burst.size / 2

    def ring(count: int, inner: float, outer: float, color: str, turn: float) -> str:
        sparks = []
        for i in range(count):
            a = math.tau * i / count + turn
            for k, size, op in ((0, 1.0, 0.95), (1, 0.7, 0.6), (2, 0.5, 0.35), (3, 0.4, 0.2)):
                at = outer - (outer - inner) * k / 4
                x, y = math.cos(a) * at * r, math.sin(a) * at * r
                dot = max(0.7, r * 0.016 * size)
                sparks.append(
                    f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{dot:.1f}' fill='{color}' "
                    f"opacity='{op}'/>"
                )
        return "".join(sparks)

    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{burst.size}' height='{burst.size}' "
        f"viewBox='{-r:.0f} {-r:.0f} {burst.size} {burst.size}'>"
        "<defs><radialGradient id='g'>"
        f"<stop offset='0' stop-color='{burst.outer}' stop-opacity='.35'/>"
        f"<stop offset='1' stop-color='{burst.outer}' stop-opacity='0'/>"
        "</radialGradient></defs>"
        f"<circle r='{r * 0.45:.0f}' fill='url(#g)'/>"
        f"{ring(burst.rays, 0.45, 0.95, burst.outer, 0)}"
        f"{ring(burst.rays // 2, 0.2, 0.5, burst.inner, math.pi / burst.rays)}"
        "</svg>"
    )


def bursts(rng: random.Random) -> list[Burst]:
    """Four fireworks, spread over the window and clear of the sidebar."""
    spots = [(20, 16), (44, 30), (67, 12), (86, 34)]
    rng.shuffle(spots)
    out = []
    for i, (left, top) in enumerate(spots):
        outer = COLORS[i % 2]  # gold, every one
        inner = rng.choice(COLORS[2:])
        out.append(
            Burst(
                size=rng.choice((220, 260, 300)),
                left=left + rng.uniform(-3, 3),
                top=top + rng.uniform(-4, 4),
                outer=outer,
                inner=inner,
                rays=rng.choice((18, 20, 22)),
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
