from day1.skills.base import Skill


SKILLS = (
    Skill(
        name="research",
        description="联网检索、网页阅读和来源整理。",
        when_to_use="用户询问实时信息、新闻、价格、政策、网页资料，或需要核验不确定信息时。",
        instructions=(
            "不知道具体 URL 时，先调用 web_search 搜索高相关结果。",
            "用户提供具体 URL，或搜索结果中有需要深入阅读的网页时，调用 fetch_url。",
            "回答涉及网页资料时，必须附上来源链接；不要编造来源。",
        ),
        tool_names=("web_search", "fetch_url"),
    ),
    Skill(
        name="weather",
        description="查询真实天气、气温、降雨、风力和天气预报。",
        when_to_use="用户询问当前天气、明天天气、未来天气或出行天气时。",
        instructions=(
            "用户没有提供地点且问题依赖当前位置时，先调用 get_current_location 获取大致城市。",
            "查询当前天气时调用 get_weather，并将 include_forecast 设为 False。",
            "用户问明天、未来或预报时调用 get_weather，并将 include_forecast 设为 True。",
        ),
        tool_names=("get_weather", "get_current_location"),
    ),
    Skill(
        name="datetime",
        description="查询当前日期、星期、时间和基础日期时间信息。",
        when_to_use="用户询问今天几号、周几、现在几点、当前日期或当前时间时。",
        instructions=(
            "必须调用 get_current_datetime 获取实时日期时间。",
            "不要凭模型记忆或系统提示中的日期直接回答实时日期时间问题。",
        ),
        tool_names=("get_current_datetime",),
    ),
    Skill(
        name="location",
        description="查询当前网络出口 IP 对应的大致位置。",
        when_to_use="用户询问当前位置、当前城市、我在哪里，或指定 IPv4 所在地时。",
        instructions=(
            "调用 get_current_location 获取位置。",
            "回答时说明该结果基于高德 IP 定位，只能表示大致位置，不是 GPS 精确地址。",
        ),
        tool_names=("get_current_location",),
    ),
)


def get_skills() -> tuple[Skill, ...]:
    return SKILLS


def render_skills_prompt(skills: tuple[Skill, ...] | None = None) -> str:
    active_skills = skills or get_skills()
    lines = ["你拥有以下 skills。根据用户问题选择合适的 skill，并遵守对应流程："]

    for skill in active_skills:
        lines.extend(
            [
                "",
                f"Skill: {skill.name}",
                f"能力说明：{skill.description}",
                f"适用场景：{skill.when_to_use}",
            ]
        )
        if skill.tool_names:
            lines.append(f"相关工具：{', '.join(skill.tool_names)}")
        lines.append("使用流程：")
        for instruction in skill.instructions:
            lines.append(f"- {instruction}")

    return "\n".join(lines)
