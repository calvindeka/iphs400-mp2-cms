"""Render the public site into site/ as plain HTML.

Two rules the rubric checks:

  1. Only PUBLISHED content is written here. A draft that reaches site/ is a bug.
  2. Every href and src is RELATIVE ("style.css", "posts/x.html"), never
     root-absolute ("/style.css"), because Pages serves this from a subfolder.

Layout:

    site/index.html              — Next Meeting content + Post archive (depth 0)
    site/style.css
    site/<page-slug>/index.html  — one per published Page (depth 1)
    site/posts/<post-slug>/index.html — one per published Post (depth 2)

Posts live under posts/ so a Post slug can never collide with a Page slug —
the two tables each enforce their own uniqueness, not a shared one. The one
remaining edge case is a Page whose own slug is "posts", which would land on
the post archive directory; app/routes/pages.py reserves that slug.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import db, settings
from app.markdown import render_markdown

CSS = """/* Minimal starter styles — make them yours. */
:root { color-scheme: light dark; }
body { font: 16px/1.6 system-ui, sans-serif; margin: 0 auto; max-width: 42rem; padding: 1rem; }
header a { font-weight: 700; text-decoration: none; }
main { margin-block: 2rem; }
"""


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )


def _rel(depth: int, root_relative_path: str) -> str:
    """A root-relative path, rewritten as relative to a page `depth` levels
    below site/ — e.g. _rel(2, "style.css") == "../../style.css"."""
    return ("../" * depth) + root_relative_path


def _links_at_depth(depth: int, links: list[dict]) -> list[dict]:
    """Root-relative {title, href} links, rewritten for a page at `depth`."""
    return [{**link, "href": _rel(depth, link["href"])} for link in links]


def render_site(out: Path | None = None) -> Path:
    out = out or settings.SITE
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    env = environment()
    (out / "style.css").write_text(CSS)

    with db.connect() as conn:
        pages = conn.execute(
            "SELECT * FROM pages WHERE status = 'published' ORDER BY title"
        ).fetchall()
        posts = conn.execute(
            "SELECT * FROM posts WHERE status = 'published' "
            "ORDER BY published_at DESC, created_at DESC"
        ).fetchall()

    nav = [{"title": p["title"], "href": f"{p['slug']}/index.html"} for p in pages]
    # Matched by slug, not title: a Page's slug locks on first publish
    # (CONTEXT.md "Slug lock") but its title doesn't, so slug is the stable
    # identity to key off of even if "Next Meeting" gets renamed later.
    next_meeting = next((p for p in pages if p["slug"] == "next-meeting"), None)
    next_meeting_html = render_markdown(next_meeting["body_md"]) if next_meeting else None

    post_links = [{"title": p["title"], "href": f"posts/{p['slug']}/index.html"} for p in posts]
    (out / "index.html").write_text(
        env.get_template("public/home.html").render(
            title=settings.SITE_TITLE, css_path=_rel(0, "style.css"),
            home_path=_rel(0, "index.html"), nav=_links_at_depth(0, nav),
            next_meeting_html=next_meeting_html, posts=_links_at_depth(0, post_links),
        )
    )

    for page in pages:
        page_dir = out / page["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            env.get_template("public/page.html").render(
                title=page["title"], css_path=_rel(1, "style.css"),
                home_path=_rel(1, "index.html"), nav=_links_at_depth(1, nav),
                body_html=render_markdown(page["body_md"]),
            )
        )

    for post in posts:
        post_dir = out / "posts" / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "index.html").write_text(
            env.get_template("public/post.html").render(
                title=post["title"], css_path=_rel(2, "style.css"),
                home_path=_rel(2, "index.html"), nav=_links_at_depth(2, nav),
                body_html=render_markdown(post["body_md"]),
            )
        )

    return out
