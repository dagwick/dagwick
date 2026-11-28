"""Helpers shared by the drawn themes (snow, Halloween, Newroz, Lunar New Year)."""

from __future__ import annotations

import re
from typing import Any

# How long a theme moves after a page loads before it comes to rest, in seconds. A
# still page costs the browser nothing, and Airflow pages often stay open all day.
SETTLE = 180


def url(svg: str) -> str:
    """The SVG as a CSS ``url()``, escaping only what a quoted data URI needs, so the
    theme stays small (spaces and single quotes are left as they are)."""
    for ch, code in (("%", "%25"), ("#", "%23"), ("<", "%3C"), (">", "%3E"), ('"', "%22")):
        svg = svg.replace(ch, code)
    return f'url("data:image/svg+xml,{svg}")'


def settle(css: dict[str, Any], seconds: float = SETTLE) -> dict[str, Any]:
    """Make each of a theme's endless animations run for about ``seconds`` and stop.

    Every animation must end where it starts (a full loop or a round trip), so nothing
    jumps when it stops. Rules inside ``@media`` blocks are left as they are.
    """
    for selector, style in css.items():
        if selector.startswith("@") or "animation" not in style:
            continue
        duration = float(re.search(r"([\d.]+)s\b", style["animation"]).group(1))
        runs = max(1, round(seconds / duration))
        style["animation"] = style["animation"].replace("infinite", str(runs))
    return css
