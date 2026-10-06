"""T06: cms publish renders exactly the published content, relative paths,
drafts never leak, Markdown is sanitized."""
from __future__ import annotations

from app import db
from app.publish import render_site


def _login(client_as, role="editor"):
    return client_as(role)


def _create_post(client, title, body_md="Body.", status="draft", category="announcement"):
    client.get("/admin/posts")
    token = client.cookies["csrf_token"]
    client.post("/admin/posts", data={
        "title": title, "body_md": body_md, "category": category, "csrf_token": token,
    })
    with db.connect() as conn:
        post = conn.execute("SELECT * FROM posts WHERE title = ?", (title,)).fetchone()
    if status == "published":
        token = client.cookies["csrf_token"]
        client.post(f"/admin/posts/{post['id']}", data={
            "title": title, "slug": post["slug"], "body_md": body_md,
            "category": category, "status": "published", "csrf_token": token,
        })
    with db.connect() as conn:
        return conn.execute("SELECT * FROM posts WHERE title = ?", (title,)).fetchone()


def _publish_next_meeting(client, body_md="When: Tuesdays. Where: the hall."):
    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE title = 'Next Meeting'").fetchone()
    client.get("/admin/pages")
    token = client.cookies["csrf_token"]
    client.post(f"/admin/pages/{page['id']}", data={
        "title": page["title"], "slug": page["slug"], "body_md": body_md,
        "status": "published", "csrf_token": token,
    })


def test_homepage_features_next_meeting_above_the_post_archive(client_as, tmp_path):
    editor = _login(client_as)
    _publish_next_meeting(editor, body_md="When: Tuesdays.")
    _create_post(editor, "Fall Meeting Reminder", status="published")

    html = (render_site(tmp_path / "site") / "index.html").read_text()
    assert "When: Tuesdays." in html
    assert "Fall Meeting Reminder" in html
    assert html.index("When: Tuesdays.") < html.index("Fall Meeting Reminder")


def test_next_meeting_stays_featured_after_being_renamed(client_as, tmp_path):
    """Matched by slug, which locks on publish — not by title, which doesn't
    (CONTEXT.md "Slug lock")."""
    editor = _login(client_as)
    _publish_next_meeting(editor, body_md="When: Tuesdays.")

    with db.connect() as conn:
        page = conn.execute("SELECT * FROM pages WHERE slug = 'next-meeting'").fetchone()
    editor.get("/admin/pages")
    token = editor.cookies["csrf_token"]
    editor.post(f"/admin/pages/{page['id']}", data={
        "title": "Our Next Gathering", "slug": page["slug"], "body_md": page["body_md"],
        "status": "published", "csrf_token": token,
    })

    html = (render_site(tmp_path / "site") / "index.html").read_text()
    assert "When: Tuesdays." in html


def test_every_published_page_appears_in_nav(client_as, tmp_path):
    editor = _login(client_as)
    html = (render_site(tmp_path / "site") / "index.html").read_text()
    for title in ("About", "Dues", "Next Meeting", "Membership"):
        assert title in html


def test_every_published_item_gets_its_own_output_file(client_as, tmp_path):
    editor = _login(client_as)
    _create_post(editor, "Fall Meeting Reminder", status="published")

    out = render_site(tmp_path / "site")
    assert (out / "about" / "index.html").exists()
    assert (out / "posts" / "fall-meeting-reminder" / "index.html").exists()
    assert "Fall Meeting Reminder" in (out / "posts" / "fall-meeting-reminder" / "index.html").read_text()


def test_draft_post_never_appears_in_site(client_as, tmp_path):
    editor = _login(client_as)
    _create_post(editor, "Secret Draft", status="draft")

    out = render_site(tmp_path / "site")
    assert not (out / "posts" / "secret-draft").exists()
    assert "Secret Draft" not in (out / "index.html").read_text()


def test_draft_page_never_appears_in_site(client_as, tmp_path):
    editor = _login(client_as)
    editor.get("/admin/pages")
    csrf_token = editor.cookies["csrf_token"]
    editor.post("/admin/pages", data={
        "title": "Secret Draft Page", "body_md": "shh", "csrf_token": csrf_token,
    })

    out = render_site(tmp_path / "site")
    assert not (out / "secret-draft-page").exists()


def test_published_html_has_only_relative_paths(client_as, tmp_path):
    editor = _login(client_as)
    _create_post(editor, "Fall Meeting Reminder", status="published")
    out = render_site(tmp_path / "site")

    for html_file in out.rglob("index.html"):
        html = html_file.read_text()
        assert 'href="/' not in html and 'src="/' not in html, html_file


def test_markdown_script_injection_is_stripped(client_as, tmp_path):
    editor = _login(client_as)
    payload = '<script>alert(1)</script><img src="x" onerror="alert(1)">'
    _create_post(editor, "Malicious Post", body_md=payload, status="published")

    out = render_site(tmp_path / "site")
    html = (out / "posts" / "malicious-post" / "index.html").read_text()
    assert "<script" not in html
    assert "onerror" not in html
