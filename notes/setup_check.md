# Setup check (CP2)

1. **Which file would you change to make /admin say something else?**
   `templates/admin/hello.html` — `app/main.py`'s `/admin` route renders that
   template as-is with no dynamic content, so the copy lives entirely in the
   template.

2. **Where would a new route for posts be registered?**
   In a new `app/routes/posts.py` module, then wired into `create_app()` in
   `app/main.py` via `app.include_router(posts.router)` — the comment at the
   bottom of `create_app()` marks exactly that spot.

3. **Why is `site/` in .gitignore?**
   It's fully generated output: `render_site()` in `app/publish.py` deletes
   and rewrites the whole directory on every `cms publish`. Committing it
   would just be committing a build artifact that's guaranteed to drift from
   its source (the database), and it's excluded from the git history checks
   the rubric runs (D5) for exactly that reason.
2.1.284 (Claude Code)
ask-matt
claude-handoff
code-review
codebase-design
diagnosing-bugs
domain-modeling
git-guardrails-claude-code
grill-me
grill-with-docs
grilling
handoff
implement
implement-spec
improve-codebase-architecture
loop-me
migrate-to-shoehorn
PINNED.md
pr
prototype
research
retro
scaffold-exercises
setup-matt-pocock-skills
setup-pre-commit
setup-ts-deep-modules
tdd
teach
to-questionnaire
to-spec
to-tickets
triage
wait-what
wayfinder
wizard
writing-beats
writing-for-agents
writing-fragments
writing-shape
