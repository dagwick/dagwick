"""A helper shared by the drawn themes (snow, Halloween, Newroz, the Lantern Festival)."""

from __future__ import annotations


def url(svg: str) -> str:
    """The SVG as a CSS ``url()``, escaping only what a quoted data URI needs, so the
    theme stays small (spaces and single quotes are left as they are)."""
    for ch, code in (("%", "%25"), ("#", "%23"), ("<", "%3C"), (">", "%3E"), ('"', "%22")):
        svg = svg.replace(ch, code)
    return f'url("data:image/svg+xml,{svg}")'
