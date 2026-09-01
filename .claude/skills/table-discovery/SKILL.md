---
name: table-discovery
description: Builds and maintains an accurate, evidence-based understanding of every table in a data project before writing SQL, Python, ETL, modeling, or BI logic against it — grain, keys, time semantics, measures, business rules, relationships, and data quality. Use this whenever a table, schema, or dataset is introduced (new table shown, "learn this table", a CREATE TABLE/sample rows pasted in, a request to query or join tables not yet understood), before generating a query or transformation over data whose grain or join cardinality isn't already confirmed, or when reviewing/debugging a query that may have a row-multiplication, fan-out, or duplicate-key bug. Keeps a compact registry across the conversation ("show registry", "what do you know about X", "validate X", "ready?") so table semantics get established once and reused, not re-derived or silently guessed every time. Once a table is fully understood (CLEAR), can also generate realistic mock data for it from the registry entry ("mock X") — useful for testing without touching the real database.
---

# Table Discovery & Registry

On invocation, before doing anything else, give one short sentence stating
what this skill is about to do — e.g. "Building an understanding of
`[table]` — grain, keys, and joins — before we use it." Then proceed.

Never guess important data semantics. Before helping with SQL, Python, ETL,
modeling, or BI logic against a table, build enough understanding of it —
through evidence first, then targeted questions — that a join or aggregation
won't silently produce the wrong numbers.

## Core behavior

When a table is introduced, inspect everything already available first:
schema, SQL, sample rows, descriptions, an existing registry entry, and
surrounding project context. Infer what's safely inferable from that
evidence, then question the user only for what's still genuinely unclear.

- Ask only what matters — skip anything already known or answerable from data.
- Batch related questions together instead of trickling them out one at a time.
- Lead with a proposed interpretation backed by evidence, and let the user
  confirm or correct it — that's less work for them than an open question.
- This skill covers the input side (what the tables actually are). If the
  conversation is really about the business ask driving the work — what
  the output should be, who it's for, what "correct" means — that's the
  `bgdlot` skill; use both together when a request arrives already paired
  with source tables.

Good:
> For `daily_mbnt`, I need to confirm 3 things:
> 1. Does one row represent date × CIF × BDS?
> 2. Can the same combination appear more than once?
> 3. Is `doanh_so` daily activity or cumulative-to-date?

Bad:
> Please provide purpose, source, grain, primary key, foreign key, dimensions, measures...

## Required understanding, per table

Work through these in priority order — grain first, since everything else
depends on it — but don't treat this as a mechanical checklist to fill in
regardless of relevance.

1. **Identity** — table name, business purpose, source/upstream system when relevant.

2. **Grain** (mandatory) — state explicitly what one row represents:
   `ONE ROW = reporting_date × customer × salesperson`. Keep questioning
   until this is clear; nothing downstream is safe to build without it.

3. **Keys** — candidate/primary key, whether it's actually unique (not just
   assumed — label unproven uniqueness `UNVERIFIED`), relevant business IDs,
   foreign/join keys.

4. **Time** — what each date field represents (snapshot vs. transaction/event
   date), grain (daily/monthly/etc.), current-period vs. historical, and
   whether measures are point-in-time, period, or cumulative.

5. **Measures & dimensions** — business measures, units/currency/scaling,
   calculated fields, cumulative vs. incremental measures, important
   dimensions/categories. Skip detailed definitions for obviously irrelevant
   technical columns.

6. **Business rules** — exclusions, filters, mappings, special cases,
   deduplication, NULL handling, calculation definitions: anything that
   could change the result if gotten wrong.

7. **Relationships** — for each relevant join: `Table A [key] → Table B [key]`
   and expected cardinality (`1:1 | 1:N | N:1 | N:N | UNKNOWN`). Flag any
   possible fan-out or row multiplication explicitly.

8. **Data quality** — material quirks only: duplicates, NULLs, missing
   dates, late-arriving data, changing mappings, unexpected multiple
   records, known-unreliable fields.

## Verification levels

Tag every non-obvious fact with how solid it is:

- **KNOWN** — confirmed by the user or documentation
- **INFERRED** — strongly suggested by the evidence (schema, sample data)
- **UNVERIFIED** — plausible, but needs a diagnostic query to confirm
- **UNKNOWN** — not enough information yet

Prefer testing over asking whenever the database can answer the question
directly — don't make the user recall something a query would settle for
certain. Generate small diagnostic queries for things like: key uniqueness,
duplicate keys, NULL rates, row counts, join cardinality, date coverage.

## The registry

Maintain a compact registry across the conversation. One entry per table:

```
TABLE: schema.table

Purpose:
Grain:
Key:
Time:
Measures:
Rules:
Joins:
Quirks:
Status: CLEAR | PARTIAL | BLOCKED
```

Keep entries concise — this is a working reference, not documentation to
polish. Update an entry in place when new information changes it; never
create a duplicate. Don't reproduce the whole registry on every turn — only
show what's relevant to the current question. If two things the user (or the
data) says conflict, flag the conflict and ask which is correct rather than
silently picking one.

## Multi-table work

Before building a transformation that joins tables, verify for each one
involved: its grain, the join keys, the relationship cardinality, the
resulting grain after the join, whether row multiplication is possible,
which table owns each measure, and whether aggregation needs to happen
before or after the join. If a proposed join looks unsafe — cardinality
that would fan out rows, or a measure that would get double-counted — stop
and explain why before generating the final code, rather than producing
something that runs but silently inflates a number.

## Readiness gate

Before generating substantial transformation code, check internally: is the
grain clear, are the keys understood, is time semantics clear, are the
needed measures understood, is join cardinality understood, are the material
business rules captured, are the major data-quality risks known?

Classify what's still open the same way as elsewhere in this workflow:

- **BLOCKER** — the code would be wrong or unsafe to write without this
  (grain unclear, key uniqueness unproven where the query relies on it,
  join cardinality unknown, a business rule that changes the numbers)
- **VERIFY** — proceed on the best current reading, but confirm before
  calling the table done
- **ASSUMPTION** — stated explicitly so it's cheap to correct later

Don't chase every open item — low-stakes unknowns (a column's exact display
label, a rarely-used dimension not needed for this task) aren't worth a
round trip and don't need a formal tag at all. But once something is
BLOCKER, it stays a stop, not a severity note: do not generate substantial
transformation code while any BLOCKER is open, regardless of how much else
about the table is understood. Only clear a BLOCKER by getting the answer
from the user or from a diagnostic query — never by deciding on your own
that it's probably fine to proceed anyway.

When a table clears this gate, say so explicitly and mark it in the
registry — this is the signal (to the user, and to any other skill relying
on this one, like `bgdlot`) that it's safe to build on:

`<table> understood — grain, keys, and joins confirmed. Status: CLEAR.`

If it can't clear yet, say that instead and name only the blocking unknowns
— not a restatement of everything still unverified.

## Mock data

Once a table is CLEAR, its registry entry is enough to generate a small,
realistic mock dataset for it — useful for testing a query or transform
without touching the real database. Offer this, don't force it: a table
someone's actively discovering usually gets used for real work next, not
synthetic testing, so this is a follow-up, not an automatic next step after
every CLEAR.

When generating mock data, build it directly from what the registry
recorded — don't re-derive or guess table shape from scratch:

- **Grain** — generate exactly that many rows for whatever combination of
  keys/dimensions you choose to include (e.g. a few dates × a few
  customers), not an arbitrary row count.
- **Keys** — respect the uniqueness constraint the registry marked KNOWN or
  INFERRED. If it's UNVERIFIED, either mock it as unique (the common case)
  or ask whether the mock should also exercise the duplicate-key case —
  don't default to duplicates without asking, since that changes what a
  downstream query is being tested against.
- **Measures/dimensions** — plausible values matching the recorded units,
  scale, and categories (a `tỷ đồng` measure shouldn't get values that look
  like raw đồng; a categorical dimension shouldn't get values outside its
  known set).
- **Business rules** — reflect known exclusions or special cases in the
  mock (e.g. include at least one NULL in a nullable field the registry
  flagged, or one row hitting a documented edge case) so the mock is
  actually useful for testing that rule, not just filler.
- **Quirks** — if the registry recorded a known data-quality issue (a
  duplicate, a NULL rate, a gap), reproduce a small instance of it in the
  mock only if the user wants to test against that quirk specifically —
  otherwise keep the mock clean by default.

Don't invent business rules or quirks that were never confirmed just to
make the mock "more realistic" — an UNVERIFIED or UNKNOWN item stays absent
from the mock's logic, not silently assumed one way.

## Commands

- **"Learn this table"** — start or resume discovery on it, update the registry.
- **"Show registry"** — display all known tables, compactly.
- **"What do you know about X?"** — show X's current entry and what's still unresolved.
- **"Validate X"** — generate diagnostic SQL for X's unverified assumptions.
- **"Forget X"** — remove X from the working registry.
- **"Mock X"** — generate mock data for X from its registry entry (X must
  be CLEAR first; if it isn't, say what's blocking instead of guessing).
- **"Ready?"** — report whether there's enough to safely start the requested
  work, listing only what's actually blocking (not every open UNVERIFIED).

## Default workflow

Given a problem or table: inspect what's already known → infer what's safe
from evidence → identify the unknowns that actually matter → ask targeted
questions (or propose a diagnostic query) → update the registry → repeat
until clear enough → give a compact summary of the understanding → proceed
with the task.

Understand the data before generating the solution.
