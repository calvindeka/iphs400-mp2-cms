# Token budget plan

(Part 5.4 of the manual.)

This account's `/model` offers Sonnet (no `opusplan`/Opus access observed in this
session — ledger rows so far are all `Sonnet 5`). Plan is adjusted from the
manual's default accordingly: Sonnet at `high` effort for planning stages
instead of Opus, Sonnet at `medium` for implementation.

| Stage | Model | Effort | Estimate (% of a 5h window) |
|---|---|---|---|
| `/research`, quick lookups | Sonnet | low | 3% |
| `/grill-with-docs`, `/to-spec`, `/to-tickets` | Sonnet | high | 20% (one unbroken session) |
| `/implement` + `/tdd` (per ticket) | Sonnet | medium | 8% |
| `/code-review` (per ticket) | Sonnet | high | 4% |

**How many 5-hour windows will the 9 tickets take?**
Grill+spec+tickets ≈ 20% of one window. Per ticket, implement+review ≈ 12%.
9 tickets × 12% ≈ 108%, i.e. roughly 1.3 windows on top of the planning
session — call it 2 windows total if nothing goes wrong.

**How much of one week is that?**
Unknown exactly since the weekly cap isn't published per-window, but the
ledger's `weekly_pct` column tracks it directly; `scripts/usage_report.py
--remaining N` gives a live FITS/TIGHT/OVER BUDGET forecast after each ticket
rather than relying on this up-front guess.

**Which stage will I cut first if I'm wrong?**
Per the manual's fix order: lower effort on `/implement` first (medium→low
rarely helps much on TDD cycles, so in practice this means dropping
`/code-review` to a lighter pass), then `/clear` more aggressively between
tickets, then split any ticket that's running long into two, before
considering Plan B (Part 9).
