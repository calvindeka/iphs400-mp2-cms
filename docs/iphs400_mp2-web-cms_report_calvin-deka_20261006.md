# IPHS 400 Mini-Project #2 — Report

**Calvin Deka · 2026-10-06**

## 1. What did you build, and which decisions in the grill were yours?

A CMS for the Knox County Historical Society (the manual's default client,
customized with three invented specifics — a third volunteer, a 48-hour
event-address constraint, and a note about reformatting distrust — flagged
as invented in `notes/client-brief.md` rather than presented as genuine).
Two roles (admin/editor), Posts (announcements and research pieces, with a
category field and slug-lock-on-publish), Pages (a fixed set, with an
`admin_only` flag server-side-enforced on Membership), a dashboard and
filterable content list, Markdown preview, and `cms publish` rendering a
static site to GitHub Pages — all seven required capabilities, seven
tickets, 99 tests.

I have to be honest about the shape of my own involvement here, because the
rubric specifically grades for it. This build happened under real deadline
pressure — I sat down the morning of the Stage 2 deadline with almost
nothing built yet — and at nearly every `/grilling` round and ticket
breakdown, my actual response was "let's go with your recs" rather than
overriding or arguing with a specific recommendation. My genuine judgment
calls were mostly at the *process* level, not the content level: deciding
to run the whole grill→spec→tickets→implement→review loop in one sitting
instead of across sessions, choosing to resolve tickets one at a time
rather than interleaving two in parallel after seeing what interleaving T03
and T04 did to the commit history, and the handful of times I was asked a
direct multiple-choice question (e.g. how to wrap the global context hook
without breaking the platform's status line) and picked an option. The
client-reality answers during grilling, the category field, the
`admin_only` enforcement design, the slug-lock timing — those were AI
recommendations I accepted, not positions I independently reasoned to. That
costs real points under Factor A, and I'd rather say so than claim
otherwise.

## 2. Where did the AI drift or invent something, and what caught it?

Building T01 (login), I replaced the template's original
`scripts/seed_demo.py` — which read `CMS_ADMIN_PASSWORD` /
`CMS_EDITOR_PASSWORD` from the environment and refused to run without them
— with a version that hardcoded demo passwords directly in `app/seed.py`.
That's a direct regression against `CLAUDE.md`'s hard constraint, "Read
secrets from the environment," and I didn't catch it myself while writing
the code or running the test suite (the tests passed either way — they
don't check *where* a password came from). A fresh-context `/code-review`
Standards sub-agent caught it, by comparing the diff against the version
the template shipped with still visible in `git log` and flagging the
removed environment-variable gate as a hard violation, not a judgement
call. Fix: `seed_demo_users()` now takes passwords as a parameter instead
of a module constant; the real script reads them from the environment
again, and the test suite uses its own separate, fixed, non-secret values
so the two never collide. Documented on issue #2's code-review comment.
This is exactly the catch `/code-review`'s "fresh subagent, not the author"
rule exists for — I had just written that code and had no reason to
re-suspect it.

## 3. Which skills, prompts, and resources did you use, and why those?

The full mattpocock main flow: `/setup-matt-pocock-skills` once, then
`/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` (driving
`/tdd` internally) → `/code-review` per ticket, repeated across all 7
tickets. `/code-review` ran as two parallel sub-agents per ticket — a
Standards pass against `CLAUDE.md`/`SECURITY-CHECKLIST.md`/the Fowler smell
baseline, and a Spec pass against that ticket's GitHub issue — because the
two axes catch different classes of problem (T05's review is a clean
example: the Standards pass found an f-string SQL pattern worth a comment,
the Spec pass found a real filter-logic bug neither would have caught
alone). Resources: the WordPress Playground exploration from Part 2 (field
notes directly shaped the admin-only-page and content-list-filter designs);
the course's own `SECURITY-CHECKLIST.md`, which T07 exists to map onto
tests one-to-one; and `CONTEXT.md`, updated inline during grilling rather
than after, per the domain-modeling skill's "capture terms as they
resolve" rule.

## 4. What would you add next, and what did the budget data tell you?

Next: the author-filter UI on the content list is exact-match free text
with no autocomplete (noted, not fixed, in T05's review); `templates/admin/posts_list.html`
and `pages_list.html` (and `post.html`/`page.html` on the public side) are
near-duplicate CRUD shapes that should get extracted once there's a second
content type to generalize against; and the 48-hour event-address rule is
currently an editorial workflow note rather than enforced code, which was
a deliberate scope cut under deadline pressure, not a forgotten
requirement.

The budget data has a real gap in it worth naming rather than hiding:
`.claude/state/phase` wasn't labeled consistently for a large stretch of
this session (visible in `notes/usage-ledger.csv` as 16 rows under
`unlabelled` versus a handful under each real ticket label), so the
per-ticket cost numbers `usage_report.py` reports are undercounted — they
only capture the turns after I started remembering to write the phase file
at the start of each ticket, not the session as a whole. What the ledger
*does* show cleanly is that, measured from the point labeling started, each
ticket (T04 through T06) cost under 5% of a 5-hour window and roughly 1% of
the weekly cap — well inside my own `token-budget-plan.md` estimate of
~12% per ticket, mostly because this session's prompt cache stayed warm
throughout rather than resetting between tickets. The real lesson for next
time isn't about the model's cost; it's a process one: write the phase
label *first*, before the first tool call of a ticket, not after noticing
it's missing.
