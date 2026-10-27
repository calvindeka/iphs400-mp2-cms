# Grill addendum — Calvin Deka — 2026-10-27

Written in response to the 2026-10-22 evaluation (`report_mp2_calvin_20261022.md`,
item A1): the original grill transcript (`iphs400_mp2-cms_chat-session_01_calvin-deka_20261006.md`)
records three rounds answered "let's go with your recs," with no independent
reasoning on the record. This does not rewrite that transcript — it stands as
what actually happened on 2026-10-06. This is a later, honest addition:
revisiting two of those decisions and giving the reasoning that was missing
the first time.

---

**Decision: the Membership page is admin-only, enforced in code rather than
hidden from the editor's navigation.**

My answer: I would enforce the admin-only restriction in code because hiding
the link still lets someone access the page through its URL. Even with only
three trusted volunteers, someone could accidentally change an important
membership or leadership record. A permission check makes sure only the
admin can edit it.

---

**Decision: no full-text search — a plain reverse-chronological archive of
published Posts instead.**

My answer: I chose a reverse-chronological archive because it keeps recent
posts easy to find and the site simple to maintain, though full-text search
could become useful as the archive grows.
