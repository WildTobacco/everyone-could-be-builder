# exchange_log

Communication channel between AI agents working on this repo.

## Protocol

Before changing anything under `.claude/skills/`:

1. **Read** the entries below, newest first — another agent may have already done
   the work, changed a convention, or left something that needs picking up.
2. **Act** on anything addressed to you or still open. If an entry conflicts with
   what you were asked to do, say so rather than silently overriding it.
3. **Append** an entry at the top of the log describing what you changed and why.

## Entry format

Newest entries go at the **top** of the log (right under this line). Keep them
short — what changed, why, and anything the next agent needs to know.

```
### YYYY-MM-DD HH:MM ICT — <agent name>
**Changed:** <files / skills touched>
**Why:** <one or two lines>
**Open / for next agent:** <anything unresolved, or "nothing">
```

Timestamps are Indochina Time (UTC+7). Sign with the model/agent name you are
running as, so entries can be told apart.

---

### 2026-09-06 10:21 ICT — Claude Opus 5 (session 01NPwi3M)
**Changed:** created this log. No skill files touched in this entry.

**Why:** requested as a shared channel so agents editing the skills in
`.claude/skills/` can see each other's work instead of overwriting it.

**State of the repo at this point** — skills on branch `claude-main`:
`bgdlot`, `caveman`, `table-discovery`, `mindful-sql-builder`,
`python-sql-bridge-generator`, `ponytail`.

Earlier work this session, for context (predates the log, recorded once here):
- `bgdlot` + `table-discovery`: BLOCKER made a hard stop — no implementation
  code while one is open; cleared only by a user answer or a diagnostic query.
- `bgdlot` ↔ `table-discovery`: cross-referenced both ways (business ask vs.
  input tables).
- `table-discovery`: added the CLEAR gate-passed cue and "mock X" data generation.
- `mindful-sql-builder`: added the ranked 7-category testing checklist.
- `python-sql-bridge-generator`: inline-SQL template, `DB_*` env names,
  `URL.create()` instead of f-string interpolation (escapes special characters
  in credentials), query-shape-agnostic output loop.
- All skills except `caveman` announce in one line what they're doing when
  invoked; `caveman` is exempt (its own rule forbids self-reference).

**Open / for next agent:**
- The dashboard work in this session used the user-level `dashboard-builder`
  skill (not in this repo). Its template changed mid-session — re-read
  `assets/dashboard-template.html` before assuming anything about it.
- Undecided with the user: KH label placement in the target-met chart
  (`renderTargetMetChart`), and whether the five `ponytail-*` sibling skills
  should also live here.
