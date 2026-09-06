# Repo notes for AI agents

## Default modes

- Activate `ponytail` in full mode for all coding tasks.
- Activate `caveman` in full mode for all responses.

## Skills

`.claude/skills/` is the sole canonical tree for skill files in this repo.
(An earlier `.AI_agent/skills/` duplicate existed briefly and has been
removed — `.claude/skills/` is what Claude Code actually auto-loads from a
checkout, so it is the only copy now.)

Before editing any file under `.claude/skills/`, read
`.AI_agent/exchange_log.md` first — another agent may have already done the
work, changed a convention, or left something open that needs picking up.
When you commit a change under that tree, include an `Agent: <your name>`
trailer in the commit message; a GitHub Action appends a timestamped log
entry automatically from that trailer.
