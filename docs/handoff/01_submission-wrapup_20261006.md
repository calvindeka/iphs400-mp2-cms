# Handoff — IPHS 400 MP2: Knox County Historical Society CMS

**Repo:** github.com/calvindeka/iphs400-mp2-cms (main) · **Date:** 2026-10-06
**Live site:** https://calvindeka.github.io/iphs400-mp2-cms/ (gh-pages branch, already enabled and built)

## Status: feature-complete, submission docs in progress

All 7 capability tickets (#2–#8) are closed on GitHub, each with a
`/code-review` findings comment (Standards + Spec axes, two parallel
sub-agents) preceding its closing commit. 99 tests pass (`uv run pytest`).
Tags `mp2-mvp` and `mp2-final` are pushed (both today — see the report for
why both land on the same date). `cms publish` + `cms deploy` have run;
real demo content exists (one published post, the four seeded pages, the
Next Meeting page has real body content).

Spec issue #1 is open — correctly. It's the reference doc, not a closeable
ticket (see its own first comment: it was accidentally auto-closed by a
stray `Closes #1` in an early commit message, then reopened).

## What's left (submission checklist)

Run `uv run python scripts/check_submission.py --stage 2` for the live
list. As of this handoff:

- ✅ README (live URL, run-locally, AI Use Statement), screenshots (12,
  `docs/screenshots/`), report (`docs/iphs400_mp2-web-cms_report_calvin-deka_20261006.md`),
  tags, tests, no secrets in history.
- ⬜ `docs/handoff/` needs this file copied in as
  `01_submission-wrapup_20261006.md` (per the manual's naming convention)
  — the coordinating session will do this right after `/handoff` returns.
- ⬜ `docs/transcripts/` needs at least one file named
  `iphs400_mp2-cms_chat-session_01_calvin-deka_20261006.md` — not yet
  written as of this handoff.
- ⚠️ `check_submission.py`'s "no root-absolute paths in HTML" check flags
  `templates/admin/*.html` (e.g. `href="/admin/posts"`). This is a false
  positive the script doesn't distinguish: those are live FastAPI routes in
  the local-only admin console (ADR-001), not the published static site —
  the actual requirement (`site/`, `templates/public/*.html`, the
  `gh-pages` branch) is clean and tested
  (`tests/test_t00.py::test_published_html_uses_relative_paths` and
  `tests/test_publish.py::test_published_html_has_only_relative_paths`).
  Deliberately not "fixed" by converting admin hrefs to relative — that
  would need the same depth-aware relative-path logic `app/publish.py`
  uses for the static export, which is unnecessary complexity for a live
  server app and not what the rubric's hard constraint is actually about.
  Documented, not silently left.

## Local environment

`.env` exists locally (gitignored, never committed) with a real
`CMS_SECRET_KEY` and real-but-local-only `CMS_ADMIN_PASSWORD` /
`CMS_EDITOR_PASSWORD` — values are not repeated here; regenerate from
`.env.example` if needed, or ask the user. `cms.db` is seeded with the
demo admin/editor plus the four fixed pages (About, Dues, Next Meeting,
Membership — admin_only) and one published post ("Fall Meeting Reminder").

## Key decisions already made (don't re-litigate)

- `CONTEXT.md` is the domain glossary — Post vs Page, slug-lock timing,
  `admin_only`, the decided-out-of-scope list (48h address automation,
  concurrent-edit locking, full-text search). Read it before touching
  domain behavior.
- Posts/Pages CRUD duplication (`app/routes/posts.py` vs `pages.py`,
  `templates/admin/post_form.html` vs `page_form.html`) was named in two
  separate code reviews and deliberately left unextracted given the
  deadline — a reasonable next refactor, not a bug.
- CSRF is `Depends(csrf.require_valid)` on every mutating route, always
  declared *after* the login/role dependency in the function signature so
  an unauthorized request 403s/redirects before it ever reaches the CSRF
  check (this ordering was itself a bug found and fixed mid-build — see
  T02's code-review comment on issue #3).

## Suggested skills for whoever picks this up next

- If finishing the submission checklist (transcript, handoff copy): no
  skill needed, just direct file writes — this is bookkeeping, not a
  flow the main skill set models.
- If the grader/instructor comes back with required fixes after Stage 2
  feedback: `/triage` to turn their feedback into agent-ready issues,
  then `/implement` per issue as usual.
- If extending the CMS with a genuinely new feature post-submission:
  resume the main flow at `/grill-with-docs` (don't skip straight to
  `/implement` — `CONTEXT.md` needs updating in lockstep with new
  decisions, same as it was for the original 7 tickets).
