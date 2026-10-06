# Knox County Historical Society CMS

A small CMS for a three-volunteer historical society: short recurring meeting
announcements and occasional long-form research pieces, published to a static
public site.

## Language

**Post**:
Dated content with a title, slug, Markdown body, draft/published status,
author, and timestamps. Lives in the public archive/feed, newest first. Covers
both Karen's meeting announcements and Tom's research pieces — same content
type, same lifecycle.
_Avoid_: Article, announcement (as a separate type — it isn't one).

**Page**:
Undated content that appears in the public site's navigation once published.
Reserved for a small fixed set: About, Dues, Next Meeting, Membership.
_Avoid_: Post.

**admin_only (Page flag)**:
A Page flagged this way can only be created/edited/deleted by the admin role;
editors can manage every other Page freely. Set on the Membership page because
"nobody but Tom edits the membership page" is a hard client rule, enforced in
code per the Security Checklist (not by hiding the link).

**Next Meeting page**:
The one persistent Page Karen edits in place (not a new Post each time) to
answer "when/where/agenda" from the homepage without scrolling the archive.

**Slug lock**:
A Post/Page's slug is freely editable while it is a draft, and frozen the
moment it is first published — preserves "permanent, memorable URLs" once
shared.

**Admin console**:
The private, local-only app at `/admin`. UI chrome avoids the word "Admin" for
users in the editor role (shown as "Dashboard"/"Content" instead) since Priya
specifically avoids anything labeled "admin"; sections truly restricted to the
admin role keep "Admin" language.
_Avoid_: Backend, dashboard (as the umbrella term — "Admin console" is the
umbrella; "Dashboard" is only the editor-facing relabel of it).

## Decided rules (carry into spec)

- **Last-admin lockout**: deactivating or demoting the sole remaining admin
  is blocked with a clear error. Tom is the only admin; an accidental
  lockout has no recovery path.
- **Content-list visibility**: every admin/editor sees every Post/Page in
  the admin console's list, regardless of author. "Filter by author" is one
  filter among several, not a privacy wall.
- **User provisioning**: no self-signup, no email/reset-link flow (ADR-001
  keeps everything off the internet). The admin sets a new user's initial
  password directly and shares it out-of-band.

**Category (Post field)**:
A lightweight tag on Post — Announcement or Research, extensible later.
Answers the client-brief complaint that Tom's pieces get lost in Karen's
weekly announcements; doubles as a content-list filter dimension (capability
5) alongside draft/published and author.

## Out of scope (decided, not silently dropped)

- **48-hour event-address visibility**: not automated. Editorial workflow —
  Karen/Tom leave the address blank until 48h before the event. No scheduled-
  visibility code, no test for it.
- **Concurrent-edit locking** (seen in WordPress Playground field notes):
  skipped. Last-write-wins. Team is three people; collision risk is low.
- **Full-text search**: skipped. The stated problem ("Facebook isn't
  searchable") is solved by a plain reverse-chronological public archive of
  all published Posts, no pagination cap — a real improvement over a Facebook
  feed without building a search index.
