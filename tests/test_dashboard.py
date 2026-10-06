"""T05: dashboard counts, the combined filterable content list, and preview."""
from __future__ import annotations

from conftest import DEMO_USERS


def _create_post(client, title, category="announcement"):
    client.get("/admin/posts")
    token = client.cookies["csrf_token"]
    client.post("/admin/posts", data={
        "title": title, "body_md": "Body.", "category": category, "csrf_token": token,
    })


def _create_page(client, title):
    client.get("/admin/pages")
    token = client.cookies["csrf_token"]
    client.post("/admin/pages", data={"title": title, "body_md": "Body.", "csrf_token": token})


def test_dashboard_shows_counts(client_as):
    editor = client_as("editor")
    _create_post(editor, "A Post")
    response = editor.get("/admin")
    assert response.status_code == 200
    assert "Posts: 1" in response.text
    assert "Pages: 4" in response.text  # the four fixed seed pages
    assert "Users: 2" in response.text  # admin + editor; deactivated excluded


def test_content_list_shows_posts_and_pages_together(client_as):
    editor = client_as("editor")
    _create_post(editor, "A Post")
    response = editor.get("/admin/content")
    assert response.status_code == 200
    assert "A Post" in response.text
    assert "About" in response.text  # a seeded Page


def test_content_list_filters_by_type(client_as):
    editor = client_as("editor")
    _create_post(editor, "A Post")
    response = editor.get("/admin/content", params={"type": "page"})
    assert "A Post" not in response.text
    assert "About" in response.text


def test_content_list_filters_by_status(client_as):
    editor = client_as("editor")
    _create_post(editor, "A Draft Post")
    response = editor.get("/admin/content", params={"status": "published"})
    assert "A Draft Post" not in response.text
    assert "About" in response.text  # seeded pages are published


def test_content_list_filters_by_category(client_as):
    editor = client_as("editor")
    _create_post(editor, "An Announcement", category="announcement")
    _create_post(editor, "A Research Piece", category="research")
    response = editor.get("/admin/content", params={"category": "research"})
    assert "A Research Piece" in response.text
    assert "An Announcement" not in response.text
    assert "About" not in response.text  # pages have no category, excluded


def test_content_list_explicit_type_page_wins_over_a_stray_category(client_as):
    """type=page must still show pages even if a leftover category value is
    present (e.g. from a form that didn't clear it when type changed)."""
    editor = client_as("editor")
    response = editor.get("/admin/content", params={"type": "page", "category": "research"})
    assert "About" in response.text


def test_dashboard_users_count_excludes_deactivated(client_as):
    response = client_as("admin").get("/admin")
    assert "Users: 2" in response.text  # admin + editor only, not the deactivated seed account


def test_content_list_filters_by_author_and_shows_every_authors_items(client_as):
    editor = client_as("editor")
    admin = client_as("admin")
    _create_post(editor, "Editor Post")
    _create_post(admin, "Admin Post")

    as_editor = editor.get("/admin/content", params={"author": DEMO_USERS["admin"]["email"]})
    assert "Admin Post" in as_editor.text
    assert "Editor Post" not in as_editor.text

    unfiltered = editor.get("/admin/content")
    assert "Admin Post" in unfiltered.text and "Editor Post" in unfiltered.text


def test_logged_in_user_can_preview_a_draft_post(client_as):
    editor = client_as("editor")
    _create_post(editor, "Draft Preview Post")
    response = editor.get("/admin/content")
    import re
    post_id = re.search(r"/admin/posts/(\d+)/preview", response.text).group(1)
    preview = editor.get(f"/admin/posts/{post_id}/preview")
    assert preview.status_code == 200
    assert "Draft Preview Post" in preview.text


def test_anonymous_cannot_preview_a_post(client_as, client):
    editor = client_as("editor")
    _create_post(editor, "Private Draft")
    response = editor.get("/admin/content")
    import re
    post_id = re.search(r"/admin/posts/(\d+)/preview", response.text).group(1)
    anon = client.get(f"/admin/posts/{post_id}/preview", follow_redirects=False)
    assert anon.status_code in (302, 303)
