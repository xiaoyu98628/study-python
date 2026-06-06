---
name: sandbox
description: Use this skill when the user asks to run untrusted code, execute commands in isolation, test scripts safely, install temporary dependencies, inspect files inside a sandbox, or use an isolated remote execution environment.
---

# Sandbox

## Instructions

When using this skill:

1. Use sandbox tools for risky or untrusted execution instead of running code locally.
2. Use `sandbox_run` to execute commands.
3. Use `sandbox_write_file` before running generated code that needs a file.
4. Use `sandbox_read_file` to inspect files or outputs in the sandbox.
5. Use `sandbox_stop` when the sandbox is no longer needed.
6. Keep commands focused and avoid long-running background processes in the first version.

## Tools

- sandbox_run
- sandbox_write_file
- sandbox_read_file
- sandbox_stop
