# Repo notes for AI agents

## Skills

`.AI_agent/skills/` is the sole canonical tree for skill files in this repo
(`.claude/skills/` was removed as a redundant duplicate).

Before editing any file under `.AI_agent/skills/`, read
`.AI_agent/skills/exchange_log.md` first — another agent may have already
done the work, changed a convention, or left something open that needs
picking up. When you commit a change under that tree, include an
`Agent: <your name>` trailer in the commit message; a GitHub Action appends
a timestamped log entry automatically from that trailer.
