---
name: dashboard-pipeline
description: Runs the full end-to-end dashboard build as a staged, resumable pipeline — URD discovery, table learning, a durable data-model file, calculations, parallel per-tab visualization work, and assembly — delegating the mechanical stages to subagents while keeping judgment in the main session. Use this to start a new dashboard from a URD/requirements document or a set of source tables, to resume a dashboard build in a later chat session, or whenever a dashboard task is large enough to need more than one stage. This is the conductor for `bgdlot`, `table-discovery`, and `dashboard-builder`; invoke it instead of those three individually when building a whole dashboard rather than answering a single question.
---

# Dashboard Pipeline

On invocation, before doing anything else, give one short sentence stating
where the pipeline is starting or resuming — e.g. "Resuming the dashboard
pipeline at stage 4; `data_model.md` is present and the tables are CLEAR."
Then proceed.

This skill does not re-implement discovery, table learning, or chart
rendering — three existing skills already do those. It sequences them,
decides what gets delegated, and writes the two files that let a build
survive the end of a chat session.

## Why the files matter

A subagent starts cold and disappears when it finishes. It carries nothing
into the next stage, and nothing into tomorrow's session. The `table-discovery`
registry has the same limit by design — it lives "across the conversation,"
and the conversation ends.

So everything a later stage or a later session needs is written to disk:

- **`data_model.md`** — the durable spill of the table-discovery registry.
  Grain, keys, columns, units, joins, cardinality, business rules, quirks.
  Every calculation and every chart reads this before doing anything.
- **`lineage.md`** — appended to as the work happens, never reconstructed
  afterwards. An agent at the end of the pipeline cannot recover lineage it
  never observed.

Both live alongside the dashboard output, not in a scratch directory.

Write `data_model.md` as a table, not prose — `column | type | grain | unit |
source | notes`. Prose gets skimmed and hallucinated around; the classic
parallel-stage failure is two agents inventing two different names for the
same field, or one assuming `tỷ` where another assumed raw đồng.

## Stages

Sequential unless marked otherwise. Each stage names who runs it.

**1. Business ask — main session.** Read the URD. Run the `bgdlot` skill to
turn it into a clear data problem. Do not delegate: this is where the
judgment is, and a BLOCKER here invalidates everything downstream. Honor
`bgdlot`'s own stop rule — an open BLOCKER halts the pipeline here.

**2. Source tables — main session, or one subagent per table.** Run
`table-discovery` until every table needed is CLEAR. Delegate only when
there are several independent tables; a single table is faster inline.
Do not proceed while any table is BLOCKED.

**3. Write `data_model.md` — one subagent.** Spill the registry to disk in
the column-table format above. Review the result yourself before anything
downstream consumes it: a wrong grain here poisons every number in every
chart, and it is cheap to catch now and expensive to catch after four tabs
are built. Append the source→understanding step to `lineage.md`.

**4. Calculations and metrics — one or two subagents.** Build the transforms
and metric definitions from `data_model.md`. Where the work is SQL, the
`mindful-sql-builder` skill applies. Each agent appends its
input → transform → output to `lineage.md`.

**5. Visualizations — parallel, one subagent per tab.** This is the only
genuinely parallel stage, and it needs two rules to be safe:

- **Spawn the whole batch in a single message.** Several Agent calls in one
  message run concurrently; the same calls spread across several messages
  run one after another and waste the stage.
- **Give every agent its own output file.** Never let two concurrent agents
  write the same file — the last write silently wins and the other tab's
  work vanishes. Each writes a fragment (`tab1_charts.html`), and assembly
  happens in stage 6.

**6. Assembly — main session.** Compose the fragments into the dashboard
using `dashboard-builder` and its template conventions. Keep this in the
main session: it needs the accumulated feedback about layout, spacing, and
what the user has already rejected, which no cold agent has.

**7. Lineage close-out — main session.** Verify `lineage.md` covers every
transform that actually ran. If a stage skipped its append, fix it from the
diff while the work is still recent.

## Delegating

A subagent cannot see this conversation, the URD, or any other agent. Every
spawn prompt carries, explicitly:

- What is being built and why — enough that the agent can make a judgment
  call rather than follow a narrow instruction into a wrong result.
- The absolute path to `data_model.md`, and an instruction to read it first.
- The absolute path of its own output file, and that it writes nowhere else.
- For chart work: read `.claude/skills/dashboard-builder/SKILL.md` and
  follow the template's conventions. A terse prompt produces a generic
  chart that ignores every BIDV convention in that skill.
- A closing instruction to append its lineage line and to report the columns
  and units it actually used.

That last item is the cheap verification: a returned "columns referenced:
`doanh_so`, `loi_nhuan`; unit assumed: tỷ" can be diffed against
`data_model.md` in seconds. Discovering a unit mismatch by eye, four tabs
later, cannot.

Use Sonnet for the mechanical stages (3, 4, 5). Keep the main session on the
stronger model — stages 1, 2, 6, and 7 are where a wrong call is expensive.

## Resuming in a later session

The pipeline is meant to span sessions. On invocation, check what already
exists on disk before assuming a cold start:

- No `data_model.md` → start at stage 1.
- `data_model.md` present, no fragments → resume at stage 4.
- Some fragments present → resume at stage 5, spawning only the missing tabs.
- All fragments present → resume at stage 6.

State which stage you are resuming at and why, and never silently redo a
completed stage — re-running stage 3 over a reviewed `data_model.md` can
quietly replace a corrected grain with a freshly guessed one.

## Gate

Before stage 5 — the expensive, parallel one — confirm: every table CLEAR,
`data_model.md` reviewed by the user, metric definitions settled, and each
tab's spec known. Four agents built on an unreviewed data model produce four
tabs of confidently wrong numbers, and the cost of that is discovered last.
