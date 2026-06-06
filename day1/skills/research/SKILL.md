---
name: research
description: Use this skill when the user asks for current facts, web research, news, policies, prices, web page content, source-backed answers, or information that may be outdated or uncertain.
---

# Research

## Instructions

When using this skill:

1. If the user does not provide a specific URL, call `web_search` first to find relevant sources.
2. If the user provides a URL, or a search result needs deeper reading, call `fetch_url`.
3. Prefer reliable and directly relevant sources.
4. Include source links when the answer uses web information.
5. Do not invent sources.

## Tools

- web_search
- fetch_url
