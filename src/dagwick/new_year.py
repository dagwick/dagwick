"""New Year for the whole Airflow UI, drawn with CSS only (used by the New Year theme).

Fireworks burst in the upper part of the window, each on its own rhythm: it blooms,
droops a little as if pulled down, and fades. Confetti and gold glitter drift down in
two layers at different speeds, some confetti has settled on top of the cards, and a
warm glow rises from the bottom of the window. Everything moves with CSS transforms and
opacity, which the graphics card does without repainting the page. Viewers who prefer
reduced motion get a still scene. Airflow's sidebar stays above the decorations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from dagwick.halloween import SIDEBAR, TOP
from dagwick.snow import CAP_H, CAPPED, EDGE, INSIDE, VARIANTS, url

SEED = 1231

# Bright on Airflow's dark page, and still visible on the light one.
COLORS = ("#fbbf24", "#f472b6", "#22d3ee", "#a78bfa", "#4ade80", "#fb7185", "#facc15")
GOLD = ("#fde68a", "#fbbf24", "#f59e0b")


def _move(x: float, y: float, scale: float = 1.0) -> str:
    return f"translate3d({x:.0f}px, {y:.0f}px, 0) scale({scale:.2f})"


# ---- fireworks ----

# Elements whose free ::before/::after carry one firework each; they exist on every
# Airflow page (the same ones Halloween uses for its bats).
BURST_HOSTS = (
    "html::after",
    "body::after",
    '[data-testid="nav-sidebar"]::before',
    '[data-testid="nav-sidebar"]::after',
    '[data-testid="nav-home-link"]::before',
    '[data-testid="nav-dags-link"]::before',
)


@dataclass(frozen=True)
class Burst:
    size: int  # px
    left: float  # vw, where the centre is
    top: float  # vh
    outer: str  # colour of the long rays
    inner: str  # colour of the short rays
    rays: int
    seconds: float
    delay: float  # negative: the cycle has already started when the page opens


def burst_svg(burst: Burst) -> str:
    """One firework: rays of sparks fading towards the centre, and a soft glow."""
    r = burst.size / 2

    def ring(count: int, inner: float, outer: float, color: str, turn: float) -> str:
        sparks = []
        for i in range(count):
            a = math.tau * i / count + turn
            for step, (k, size, op) in enumerate(((0, 1.0, 1), (1, 0.75, 0.7), (2, 0.5, 0.45))):
                at = outer - (outer - inner) * k / 3
                x, y = math.cos(a) * at * r, math.sin(a) * at * r
                dot = max(0.8, r * 0.022 * size) * (1.2 if step == 0 else 1)
                sparks.append(
                    f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{dot:.1f}' fill='{color}' "
                    f"opacity='{op}'/>"
                )
        return "".join(sparks)

    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{burst.size}' height='{burst.size}' "
        f"viewBox='{-r:.0f} {-r:.0f} {burst.size} {burst.size}'>"
        "<defs><radialGradient id='g'>"
        f"<stop offset='0' stop-color='{burst.inner}' stop-opacity='.55'/>"
        f"<stop offset='1' stop-color='{burst.inner}' stop-opacity='0'/>"
        "</radialGradient></defs>"
        f"<circle r='{r * 0.32:.0f}' fill='url(#g)'/>"
        f"{ring(burst.rays, 0.5, 0.95, burst.outer, 0)}"
        f"{ring(burst.rays // 2, 0.22, 0.55, burst.inner, math.pi / burst.rays)}"
        "</svg>"
    )


def bursts(rng: random.Random) -> list[Burst]:
    """Six fireworks spread over the upper part of the window, clear of the sidebar."""
    lefts = [18, 32, 47, 61, 75, 88]
    rng.shuffle(lefts)
    out = []
    for i, left in enumerate(lefts):
        outer, inner = rng.sample(COLORS, 2)
        out.append(
            Burst(
                size=rng.choice((150, 180, 210, 240)),
                left=left + rng.uniform(-4, 4),
                top=rng.uniform(10, 38),
                outer=outer,
                inner=inner,
                rays=rng.choice((14, 16, 18)),
                seconds=round(rng.uniform(5.5, 8.5), 1),
                delay=-round(i * 1.3 + rng.uniform(0, 1), 1),
            )
        )
    return out


def fireworks(rng: random.Random) -> dict[str, Any]:
    """Each firework blooms, droops and fades, then waits for its next turn."""
    css: dict[str, Any] = {
        ", ".join(BURST_HOSTS): {
            "content": '""',
            "position": "fixed",
            "pointerEvents": "none",
            "zIndex": TOP,
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
        droop = b.size * 0.08
        css[f"@keyframes {name}"] = {
            "0%": {"opacity": "0", "transform": _move(0, 0, 0.1)},
            "5%": {"opacity": "1", "transform": _move(0, 0, 0.4)},
            "28%": {"opacity": "0.95", "transform": _move(0, droop / 3, 1)},
            "50%": {"opacity": "0", "transform": _move(0, droop, 1.06)},
            "100%": {"opacity": "0", "transform": _move(0, droop, 1.06)},
        }
    return css


# ---- confetti ----


@dataclass(frozen=True)
class Layer:
    host: str
    width: int
    height: int
    count: int
    scale: tuple[float, float]
    seconds: float


LAYERS = (
    Layer("html::before", 1031, 613, 26, (0.6, 0.9), 30),
    Layer("#root::after", 1213, 1009, 18, (1.0, 1.4), 21),
)
SWAY = 22


def piece(rng: random.Random, scale: float) -> str:
    """One bit of confetti: a paper strip, a dot, a curl of streamer or gold glitter."""
    color = rng.choice(COLORS)
    kind = rng.random()
    if kind < 0.45:
        w, h = 4 * scale, 9 * scale
        return (
            f"<rect x='{-w / 2:.1f}' y='{-h / 2:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"rx='1' fill='{color}'/>"
        )
    if kind < 0.65:
        return f"<circle r='{2.6 * scale:.1f}' fill='{color}'/>"
    if kind < 0.8:
        s = 6 * scale
        return (
            f"<path d='M{-s:.1f} 0 q{s / 2:.1f} {-s:.1f} {s:.1f} 0 t{s:.1f} 0' fill='none' "
            f"stroke='{color}' stroke-width='{1.6 * scale:.1f}' stroke-linecap='round'/>"
        )
    gold = rng.choice(GOLD)
    s = 3.2 * scale
    star = (  # a four-pointed glint
        f"M0 {-s:.1f} L{s / 3:.1f} 0 L0 {s:.1f} L{-s / 3:.1f} 0Z "
        f"M{-s:.1f} 0 L0 {s / 3:.1f} L{s:.1f} 0 L0 {-s / 3:.1f}Z"
    )
    return f"<path d='{star}' fill='{gold}'/>"


def confetti_svg(rng: random.Random, layer: Layer) -> str:
    """One repeat of a layer; a piece near an edge is also drawn on the other side."""
    w, h = layer.width, layer.height
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>"]
    for _ in range(layer.count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        shape = piece(rng, rng.uniform(*layer.scale))
        turn, op = rng.uniform(0, 360), rng.uniform(0.55, 0.9)
        reach = 16
        for px in [x] + [x + d for d in (-w, w) if abs(x + d - w / 2) < w / 2 + reach]:
            for py in [y] + [y + d for d in (-h, h) if abs(y + d - h / 2) < h / 2 + reach]:
                out.append(
                    f"<g transform='translate({px:.0f} {py:.0f}) rotate({turn:.0f})' "
                    f"opacity='{op:.2f}'>{shape}</g>"
                )
    out.append("</svg>")
    return "".join(out)


def confetti(rng: random.Random) -> dict[str, Any]:
    """Two layers of confetti falling at different speeds, swaying side to side."""
    css: dict[str, Any] = {}
    for i, layer in enumerate(LAYERS):
        name = f"dagwickConfetti{i}"
        side = f"-{SWAY * 2}px"
        css[layer.host] = {
            "content": '""',
            "position": "fixed",
            "top": f"-{layer.height}px",
            "bottom": "0",
            "left": side,
            "right": side,
            "pointerEvents": "none",
            "zIndex": TOP,
            "backgroundImage": url(confetti_svg(rng, layer)),
            "backgroundSize": f"{layer.width}px {layer.height}px",
            "willChange": "transform",
            "animation": f"{name} {layer.seconds}s linear infinite",
        }
        h = layer.height
        css[f"@keyframes {name}"] = {
            "0%": {"transform": _move(0, 0)},
            "25%": {"transform": _move(SWAY, h / 4)},
            "50%": {"transform": _move(0, h / 2)},
            "75%": {"transform": _move(-SWAY, h * 3 / 4)},
            "100%": {"transform": _move(0, h)},
        }
    return css


# ---- confetti settled on the cards ----


def settled_svg(seed: int, width: int) -> str:
    """One repeat of confetti lying along a card's top edge."""
    rng = random.Random(seed)
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{CAP_H}' "
        f"viewBox='0 0 {width} {CAP_H}'>"
    ]
    for _ in range(rng.randint(5, 8)):
        x = rng.uniform(8, width - 8)
        y = EDGE - rng.uniform(1.5, 3.5)  # resting on the edge
        turn = rng.choice((rng.uniform(-25, 25), rng.uniform(65, 115)))  # mostly lying flat
        out.append(
            f"<g transform='translate({x:.0f} {y:.1f}) rotate({turn:.0f})' opacity='.9'>"
            f"{piece(rng, rng.uniform(0.7, 1.0))}</g>"
        )
    out.append("</svg>")
    return "".join(out)


def settled() -> dict[str, Any]:
    """Confetti on each card's top edge, in five random variants spread over the cards."""
    css: dict[str, Any] = {'[data-testid="card-list"]': {"paddingTop": f"{EDGE}px"}}
    for sel in CAPPED:
        css[sel] = {"position": "relative"}
        css[f"{sel}::after"] = {
            "content": '""',
            "position": "absolute",
            "top": "-1px" if sel in INSIDE else f"-{EDGE}px",
            "left": "4px",
            "right": "4px",
            "height": f"{CAP_H}px",
            "backgroundRepeat": "repeat-x",
            "pointerEvents": "none",
            "zIndex": "1",
        }
    for k in range(VARIANTS):
        rng = random.Random(4000 + k)
        width = rng.randint(260, 420)
        key = ", ".join(f"{pick(k + 1)}::after" for pick in CAPPED.values())
        css[key] = {
            "backgroundImage": url(settled_svg(5000 + k, width)),
            "backgroundSize": f"{width}px {CAP_H}px",
            "backgroundPosition": f"{rng.randint(0, width)}px 0",
        }
    return css


def global_css() -> dict[str, Any]:
    """New Year as Airflow theme ``globalCss`` (selector -> style)."""
    rng = random.Random(SEED)
    moving = [*BURST_HOSTS, *(layer.host for layer in LAYERS)]
    return {
        **settled(),
        **confetti(rng),
        **fireworks(rng),
        # A warm glow rising from the bottom, and a faint night sky at the top.
        "body::before": {
            "content": '""',
            "position": "fixed",
            "inset": "0",
            "pointerEvents": "none",
            "zIndex": TOP,
            "backgroundImage": (
                "linear-gradient(to top, rgba(251, 191, 36, 0.16), transparent 140px), "
                "radial-gradient(ellipse at top, rgba(76, 29, 149, 0.2), transparent 55%)"
            ),
        },
        "html.light body::before": {
            "backgroundImage": (
                "linear-gradient(to top, rgba(245, 158, 11, 0.12), transparent 140px), "
                "radial-gradient(ellipse at top, rgba(124, 58, 237, 0.08), transparent 55%)"
            ),
        },
        # Keep Airflow's sidebar (and its user menu) above the decorations. Airflow's own
        # style for the sidebar outranks theme styles, hence !important.
        '[data-testid="nav-sidebar"]': {"zIndex": f"{SIDEBAR} !important"},
        # Reduced motion: confetti stands still and the fireworks show as still bursts.
        "@media (prefers-reduced-motion: reduce)": {
            **{sel: {"animation": "none"} for sel in moving},
            ", ".join(BURST_HOSTS): {"animation": "none", "opacity": "0.5", "transform": "none"},
        },
    }
