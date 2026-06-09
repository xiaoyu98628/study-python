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

## Prompt 预览

查看最终发送给模型的 system prompt：

```bash
uv run python -m day1.prompts.preview
```

该命令会按当前项目的组合逻辑输出完整 system prompt，包括：

- `day1/prompts/system.md`
- `day1/prompts/context.md`
- `storage/app/context/context.json`
- `day1/prompts/tools.md`
- skills metadata

如果只想在输出末尾额外查看 prompt 长度统计：

```bash
uv run python -m day1.prompts.preview --stats
```

输出末尾会包含：

```text
--- stats ---
characters: 2986
```

## Context 配置

运行时 context 文件位于：

```text
storage/app/context/context.json
```

它会被注入到最终 system prompt 中，作为模型理解用户偏好和当前项目背景的参考信息。可参考同目录模板：

```text
storage/app/context/context.example.json
```

如果需要临时禁用某些 skills，可以在 `project_context.disabled_skills` 中配置 skill 名称。例如：

```json
{
  "project_context": {
    "disabled_skills": ["sandbox"]
  }
}
```

禁用后的 skill 不会出现在最终 system prompt 的 skills metadata 中。

校验 context 文件结构：

```bash
uv run python -m day1.context --validate
```

通过时会输出：

```text
OK
```

如果要校验其他路径的 context 文件：

```bash
uv run python -m day1.context --validate --path storage/app/context/context.example.json
```

## Sandbox

项目支持两种 sandbox provider：

- `daytona`：远程 sandbox provider。
- `docker`：本机 Docker 容器 sandbox provider。

需要在 `.env` 中配置：

```env
SANDBOX_PROVIDER="daytona"
DAYTONA_API_KEY=""
DAYTONA_API_URL=""
DAYTONA_TARGET=""
```

其中 `DAYTONA_API_KEY` 必填；`DAYTONA_API_URL` 和 `DAYTONA_TARGET` 可以按 Daytona 账号配置填写。

如果要使用本机 Docker sandbox：

```env
SANDBOX_PROVIDER="docker"
DOCKER_SANDBOX_IMAGE="python:3.13-slim"
DOCKER_SANDBOX_NETWORK="none"
DOCKER_SANDBOX_MEMORY="512m"
DOCKER_SANDBOX_CPUS="1.0"
DOCKER_SANDBOX_CONTAINER_PREFIX="day1-sbx-"
```

Docker sandbox 会为当前会话创建一个容器，宿主机只挂载：

```text
storage/sandboxes/<session-id> -> /workspace
```

默认安全策略：

- 容器内以 `1000:1000` 非 root 用户运行。
- 默认禁用网络：`DOCKER_SANDBOX_NETWORK="none"`。
- 根文件系统只读，只开放 `/workspace` 和 `/tmp` 写入。
- drop 所有 Linux capabilities，并启用 `no-new-privileges`。
- `sandbox_read_file` 和 `sandbox_write_file` 只能访问 `/workspace` 内路径，不能通过 `..` 逃逸。

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

测试样例：
```text
USER：今天上海天气怎么样？需要带伞吗？
USER：帮我搜索一下 LangChain 最新版本有什么变化，并附来源
USER：读取 README.md，总结这个项目现在有哪些能力
USER：写一个 Python 脚本计算 1 到 100 的和，在 sandbox 里运行
USER：搜索 Python 3.14 的新特性，整理成 5 点
```
