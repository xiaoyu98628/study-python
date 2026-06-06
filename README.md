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
