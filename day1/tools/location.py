import ipaddress

import httpx
from langchain.tools import tool
from pydantic import BaseModel, Field

from config.config import config


class CurrentLocationInput(BaseModel):
    ip: str = Field(default="", description="可选 IPv4 地址；不填时使用当前网络出口 IP")


def _validate_ipv4(ip: str) -> str:
    ip = ip.strip()
    if not ip:
        return ""

    try:
        value = ipaddress.ip_address(ip)
    except ValueError as exc:
        raise RuntimeError("ip 必须是合法的 IPv4 地址") from exc

    if value.version != 4:
        raise RuntimeError("高德 IP 定位仅支持 IPv4 地址")

    return ip


def _format_value(value: object) -> str:
    if isinstance(value, list):
        return "无" if not value else "、".join(str(item) for item in value)
    if value in ("", None):
        return "无"
    return str(value)


@tool(args_schema=CurrentLocationInput)
def get_current_location(ip: str = "") -> str:
    """根据高德 IP 定位查询当前位置，适合询问当前城市、当前位置或指定 IPv4 所在地。"""
    api_key = config().tool.amap_api_key
    if not api_key:
        raise RuntimeError("缺少环境变量 AMAP_API_KEY")

    params = {
        "key": api_key,
        "output": "JSON",
    }

    checked_ip = _validate_ipv4(ip)
    if checked_ip:
        params["ip"] = checked_ip

    with httpx.Client(timeout=10) as client:
        response = client.get("https://restapi.amap.com/v3/ip", params=params)

    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        info = data.get("info") or "未知错误"
        infocode = data.get("infocode") or "unknown"
        raise RuntimeError(f"高德 IP 定位失败：{info}（infocode={infocode}）")

    province = _format_value(data.get("province"))
    city = _format_value(data.get("city"))
    adcode = _format_value(data.get("adcode"))
    rectangle = _format_value(data.get("rectangle"))

    return (
        "当前网络位置：\n"
        f"省份：{province}\n"
        f"城市：{city}\n"
        f"行政区划编码：{adcode}\n"
        f"定位范围：{rectangle}\n\n"
        "来源：高德 IP 定位。该结果基于网络出口 IP，只能表示大致位置，不是 GPS 精确地址。"
    )
