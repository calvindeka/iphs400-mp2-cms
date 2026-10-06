# Knox County Historical Society — Web CMS

A small CMS built for IPHS 400 Mini-Project #2: a local admin console
(FastAPI + Jinja + SQLite) where volunteers log in, write posts and pages,
and publish; `cms publish` renders the published content to static HTML,
deployed to GitHub Pages.

## Live URL

**https://calvindeka.github.io/iphs400-mp2-cms/**

## Run locally

```bash
git clone https://github.com/calvindeka/iphs400-mp2-cms.git
cd iphs400-mp2-cms
uv sync
cp .env.example .env
# Edit .env: set CMS_SECRET_KEY, CMS_ADMIN_PASSWORD, CMS_EDITOR_PASSWORD to
# real local values (never the placeholders) — these never leave your machine.
set -a && source .env && set +a
uv run python scripts/seed_demo.py       # seeds admin@example.test / editor@example.test
uv run cms serve                          # http://localhost:8000/admin
```

To rebuild and preview the public static export:

```bash
set -a && source .env && set +a
uv run cms publish                        # renders site/ from published rows
python3 -m http.server -d site 8001       # preview at http://localhost:8001
```

Run the test suite with `uv run pytest` (99 tests). Run
`uv run python scripts/check_submission.py --stage 2` before resubmitting
anything.

## What is here

```text
app/                live admin console: routes, auth, CSRF, db, publish
templates/admin/    admin console UI · templates/public/   static-export templates
scripts/            seed_demo.py, usage_report.py, check_submission.py
tests/               99 tests: one file per ticket + a security-checklist sweep
docs/adr/            decision records · CONTEXT.md   project glossary
notes/               client brief, field notes, token budget plan, usage ledger
```

## Deadlines

Stage 1 (`mp2-mvp` tag) and Stage 2 (`mp2-final` tag) were both tagged on
2026-10-06, the Stage 2 due date — see the report for why (both the setup
work and the full build happened in one continuous push that day).

## Generative AI Use Statement

**Models and skills.** Claude Sonnet 5, via Claude Code, for the entire
build — login/sessions through publish and security verification.
Anthropic's mattpocock skills drove the workflow: `/grill-with-docs` (client
interview, resolved into `CONTEXT.md`), `/to-spec`, `/to-tickets`,
`/implement` (which internally drives `/tdd`), and `/code-review` run as two
parallel sub-agents (a Standards pass and a Spec pass) after every ticket,
before each closing commit.

**Backends used**

| Session | Provider | Model | Notes |
|---|---|---|---|
| Entire build | anthropic | Sonnet 5 (medium/high effort) | No backend switch; `notes/usage-ledger.csv`'s `provider` column confirms `anthropic` throughout. |

**Two prompts I really sent** (verbatim):

1. *"can we start working on the project let's use the matt pocock workflow we have it installed right so let's begin, we can do the asking things and everything"* — kicked off the actual build, after the setup lab.
2. *"today is tues oct 6, i need to finish the project now, can we begin"* — restarted the session under deadline pressure and committed to the grill → spec → tickets → implement → review loop for the whole 7-capability build in one sitting.

**One real model failure.** Building T01 (login), I replaced the template's
original `scripts/seed_demo.py` — which read `CMS_ADMIN_PASSWORD` and
`CMS_EDITOR_PASSWORD` from the environment and refused to run without them —
with a version that hardcoded demo passwords directly in `app/seed.py`.
That's a direct regression against `CLAUDE.md`'s hard constraint, "Read
secrets from the environment," and I didn't catch it while writing the
code. A fresh-context `/code-review` Standards sub-agent caught it by
comparing the diff against the original stub (still visible in git history)
and flagging the removed environment-variable gate. Fix: `seed_demo_users()`
now takes passwords as a parameter; the real script reads them from the
environment again, and tests use their own separate, fixed, non-secret
values. Documented on the issue #2 code-review comment.
