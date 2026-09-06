#!/usr/bin/env python3
"""Append a concise, attributed entry to the shared AI-agent exchange log."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


LOG_PATH = Path(".claude/skills/exchange_log.md")
SKILL_PREFIX = ".claude/skills/"
ZERO_SHA = "0" * 40


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def safe_commit_range(before: str, after: str) -> tuple[str, str]:
    if not before or before == ZERO_SHA:
        try:
            before = git("rev-parse", f"{after}^")
        except subprocess.CalledProcessError:
            before = git("hash-object", "-t", "tree", "/dev/null")
    return before, after


def changed_skill_files(before: str, after: str) -> list[str]:
    names = git("diff", "--name-only", before, after).splitlines()
    return sorted(
        name
        for name in names
        if name.startswith(SKILL_PREFIX) and name != str(LOG_PATH)
    )


def identify_agent(before: str, after: str) -> str:
    messages = git("log", "--format=%B%x00", f"{before}..{after}")
    trailers = re.findall(r"^Agent:\s*(.+?)\s*$", messages, flags=re.MULTILINE)
    if trailers:
        return trailers[0].replace("\x00", "").strip()
    return os.environ.get("GITHUB_ACTOR_NAME") or git("show", "-s", "--format=%an", after)


def main() -> None:
    before, after = safe_commit_range(
        os.environ.get("GITHUB_BEFORE", ""),
        os.environ.get("GITHUB_AFTER", "HEAD"),
    )
    changed = changed_skill_files(before, after)
    if not changed:
        return

    agent = identify_agent(before, after)
    subject = git("show", "-s", "--format=%s", after).replace("`", "'")
    timestamp = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime(
        "%Y-%m-%d %H:%M ICT"
    )
    paths = ", ".join(f"`{path}`" for path in changed)
    entry = (
        f"\n### {timestamp} — {agent}\n"
        f"**Changed:** {paths}\n"
        f"**Why:** Automatically recorded from commit `{after[:7]}`: {subject}\n"
        "**Open / for next agent:** nothing\n"
    )

    log = LOG_PATH.read_text(encoding="utf-8")
    separator = "\n---\n"
    if separator not in log:
        raise RuntimeError(f"Could not find the entry separator in {LOG_PATH}")
    header, entries = log.split(separator, 1)
    LOG_PATH.write_text(header + separator + entry + entries, encoding="utf-8")


if __name__ == "__main__":
    main()
