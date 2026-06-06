# study-python

## Skills 校验

校验项目中的 skills 是否符合基础规范：

```bash
uv run python -m day1.skills.validate
```

通过时会输出：

```text
OK
```

如果存在问题，会输出 `ERROR` 或 `WARNING`，例如：

```text
ERROR day1/skills/foo/SKILL.md: frontmatter 缺少字段：name
WARNING day1/skills/bar/SKILL.md: name 与目录名不一致：name='baz', directory='bar'
```

## Sandbox

项目使用 Daytona 作为第一版远程 sandbox provider。

需要在 `.env` 中配置：

```env
SANDBOX_PROVIDER="daytona"
DAYTONA_API_KEY=""
DAYTONA_API_URL=""
DAYTONA_TARGET=""
```

其中 `DAYTONA_API_KEY` 必填；`DAYTONA_API_URL` 和 `DAYTONA_TARGET` 可以按 Daytona 账号配置填写。

sandbox skill 会按渐进式披露流程触发：模型先读取 `day1/skills/sandbox/SKILL.md`，再使用 sandbox tools。

当前提供的 sandbox tools：

```text
sandbox_run
sandbox_write_file
sandbox_read_file
sandbox_stop
sandbox_delete
sandbox_status
```

sandbox 生命周期日志会写入：

```text
storage/logs/sandbox.log
```
