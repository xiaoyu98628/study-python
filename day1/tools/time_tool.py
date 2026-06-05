from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain.tools import tool
from pydantic import BaseModel, Field


class CurrentDateTimeInput(BaseModel):
    """Input for current date and time queries."""

    timezone: str = Field(
        default="Asia/Shanghai",
        description="IANA 时区名称，例如 Asia/Shanghai、UTC、America/New_York",
    )


@tool(args_schema=CurrentDateTimeInput)
def get_current_datetime(timezone: str = "Asia/Shanghai") -> str:
    """查询当前日期、星期和时间。用户问今天几号、周几、现在几点时使用。"""
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("Asia/Shanghai")
        timezone = "Asia/Shanghai"

    now = datetime.now(tz)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]

    return (
        f"当前时区：{timezone}。"
        f"当前日期时间：{now:%Y年%m月%d日 %H:%M:%S}，{weekday}。"
    )
