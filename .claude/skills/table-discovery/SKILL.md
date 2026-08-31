---
name: table-discovery
description: Builds and maintains an accurate, evidence-based understanding of every table in a data project before writing SQL, Python, ETL, modeling, or BI logic against it — grain, keys, time semantics, measures, business rules, relationships, and data quality. Use this whenever a table, schema, or dataset is introduced (new table shown, "learn this table", a CREATE TABLE/sample rows pasted in, a request to query or join tables not yet understood), before generating a query or transformation over data whose grain or join cardinality isn't already confirmed, or when reviewing/debugging a query that may have a row-multiplication, fan-out, or duplicate-key bug. Keeps a compact registry across the conversation ("show registry", "what do you know about X", "validate X", "ready?") so table semantics get established once and reused, not re-derived or silently guessed every time.
---

# Table Discovery & Registry

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

If a missing answer could materially change correctness, keep asking. If
what's left is low-risk, proceed and state the assumption briefly rather
than blocking on documentation the task doesn't actually need.

## Commands

- **"Learn this table"** — start or resume discovery on it, update the registry.
- **"Show registry"** — display all known tables, compactly.
- **"What do you know about X?"** — show X's current entry and what's still unresolved.
- **"Validate X"** — generate diagnostic SQL for X's unverified assumptions.
- **"Forget X"** — remove X from the working registry.
- **"Ready?"** — report whether there's enough to safely start the requested
  work, listing only what's actually blocking (not every open UNVERIFIED).

## Default workflow

Given a problem or table: inspect what's already known → infer what's safe
from evidence → identify the unknowns that actually matter → ask targeted
questions (or propose a diagnostic query) → update the registry → repeat
until clear enough → give a compact summary of the understanding → proceed
with the task.

Understand the data before generating the solution.
