---
name: datetime
description: Use this skill when the user asks for today's date, the current time, weekday, current timezone-aware datetime, or simple questions that depend on the current date or time.
---

# Datetime

## Instructions

When using this skill:

1. Always call `get_current_datetime` for real-time date or time questions.
2. Do not answer current date or time questions from memory or from static prompt context.
3. Use the user's requested timezone when they provide one; otherwise use `Asia/Shanghai`.

## Tools

- get_current_datetime
