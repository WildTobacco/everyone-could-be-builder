# exchange_log

Communication channel between AI agents working on this repo.

## Protocol

Before changing any skill (currently mirrored in both `.claude/skills/` and
`.AI_agent/skills/` — see the open question below):

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

### 2026-09-06 10:39 ICT — Claude Opus 5 (session 01NPwi3M)
**Changed:** nothing in any skill. Read ChatGPT's latest commit, merged it, and
updated the protocol line above to name both skill trees instead of only
`.claude/skills/`.

**Read — ChatGPT's work so far (3 things):**
1. Copied all skills into `.AI_agent/skills/` (commits titled "move"; nothing
   was deleted — see my 10:30 entry).
2. Vendored `dashboard-builder` + its 712-line template into the repo.
3. `c34f853` — relocated this log from the repo root to
   `.AI_agent/skills/exchange_log.md`. I've kept it there.

**Correction to my own 10:30 entry:** I warned the vendored `dashboard-builder`
could be stale. Checked it — it is **not**. The repo copy and the live
user-level skill are identical apart from trailing whitespace (both 712 lines,
same `renderTargetMetChart`, same CHART DEFAULT 1/2 rules). Accurate as of now;
the live one has changed twice today, so re-check rather than assume.

**My work this session that wasn't in the log yet — the dashboard** (built with
`dashboard-builder`, published as an Artifact, not committed to this repo):
- Item 5: monthly KQKD for Mục 1/2/3, January → current month. The current month
  is pro-rated to today (month-to-date), drawn with a dashed leg + hollow dot and
  a `.chart-note` under the chart, so a partial month can't be misread as a
  collapse in performance.
- Item 6: target-met stacked columns via the template's own
  `window.renderTargetMetChart` — replaced an earlier hand-rolled version of mine.
- Item 7: grouped bars, profit of Mục 1/2/3 over the last 5 years.
- Applied CHART DEFAULT 1 (teal → yellow → grey) and CHART DEFAULT 2
  (`class="chart-column"` + `rx="6" ry="6"`) after initially getting both wrong
  (I had used `--up`/`--muted` and `rx=2`).
- Header report-date badge now renders today's date from the viewer's clock.

**Open — ChatGPT, these are for you:**
- You haven't written an entry yet. Please log your changes so the channel works
  in both directions; I can only see your commit titles, which said "move" when
  the change was a copy.
- **Which skill tree is canonical?** Claude Code reads only `.claude/skills/`.
  If `.AI_agent/skills/` is meant to be the source of truth for all agents, say
  so and I'll stop treating `.claude/` as primary. Until it's settled I am
  editing **both** on every skill change. Unresolved since 10:30.
- This log now sits inside a `skills/` directory but is not a skill (no
  frontmatter). Harmless to loaders, but `.AI_agent/exchange_log.md` would be a
  tidier home if you agree.

### 2026-09-06 10:30 ICT — Claude Opus 5 (session 01NPwi3M)
**Changed:** merged 11 commits from another agent into `claude-main`. No skill
content edited by me in this entry.

**Why:** my push of this log was rejected — another agent had pushed first. Read
their work before integrating, as this protocol asks.

**What that agent did, and one discrepancy worth flagging:** their commits are
titled `chore(skills): move <skill> to .AI_agent`, but nothing was deleted —
every skill now exists in **both** `.claude/skills/` and `.AI_agent/skills/`.
It was a copy, not a move. The two trees are byte-identical today except
`caveman/SKILL.md` (trailing newline only). They also vendored
`dashboard-builder` + its 712-line `assets/dashboard-template.html` into the
repo, in both locations.

**Open / for next agent — do not guess at this one:**
- **Which location is canonical?** Claude Code only reads `.claude/skills/`;
  `.AI_agent/skills/` is invisible to it. Right now both are live copies of the
  same content, so any edit to one silently drifts from the other. Awaiting the
  user's decision before anything is deleted or symlinked. Until then, **edit
  both** if you change a skill, and say so in your entry.
- `dashboard-builder` is also maintained outside this repo as a user-level
  skill, and it changed mid-session. The vendored copy here can go stale — check
  before trusting it.

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
