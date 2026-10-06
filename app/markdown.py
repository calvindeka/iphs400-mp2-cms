"""Markdown -> sanitized HTML, for every place content gets rendered as HTML.

CLAUDE.md: "User-written Markdown is sanitized before it is rendered
anywhere." This is the first place that's true (preview); publish (T06)
reuses this same function rather than rendering Markdown a second way.
"""
from __future__ import annotations

import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt()


def render_markdown(text: str) -> str:
    return nh3.clean(_md.render(text))
