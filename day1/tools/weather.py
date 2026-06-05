from pathlib import Path
from typing import Literal

import requests
from langchain.tools import tool
from pydantic import BaseModel, Field

from config.config import config

from paths import BASE_DIR

import time
import jwt

tool_config = config().tool

# Open PEM
private_key = Path(BASE_DIR / tool_config.qweather_private_key_path).read_text(encoding="utf-8")

payload = {
    'iat': int(time.time()) - 30,
    'exp': int(time.time()) + 3600,
    'sub': tool_config.qweather_project_id
}
headers = {
    'kid': tool_config.qweather_key_id,
}

# Generate JWT
encoded_jwt = jwt.encode(payload, private_key, algorithm='EdDSA', headers = headers)

class WeatherInput(BaseModel):
    """Input for weather queries."""

    location: str = Field(description="城市名、LocationID 或经纬度，例如：上海、101020100、121.47,31.23")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="温度单位：celsius 摄氏度，fahrenheit 华氏度",
    )
    include_forecast: bool = Field(
        default=False,
        description="是否查询未来天气；用户问明天、未来、预报时设为 True",
    )


def _api_host() -> str:
    api_host = tool_config.qweather_api_host
    if not api_host:
        raise RuntimeError("缺少环境变量 QWEATHER_API_HOST，请填写和风天气控制台里的 API Host")

    host = api_host.strip().rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = f"https://{host}"
    return host


def _headers() -> dict:
    api_token = encoded_jwt # tool_config.qweather_token
    if not api_token:
        raise RuntimeError("缺少环境变量 QWEATHER_TOKEN，请填写和风天气 JWT Token")

    return {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }


def _unit(units: str) -> str:
    return "i" if units == "fahrenheit" else "m"


def _request(path: str, params: dict) -> dict:
    url = f"{_api_host()}{path}"
    resp = requests.get(url, headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    if data.get("code") != "200":
        raise RuntimeError(f"和风天气接口错误：code={data.get('code')}，data={data}")

    return data


def _resolve_location(location: str) -> str:
    data = _request(
        "/geo/v2/city/lookup",
        {
            "location": location,
            "range": "cn",
            "number": 1,
            "lang": "zh",
        },
    )

    locations = data.get("location") or []
    if not locations:
        raise RuntimeError(f"找不到城市：{location}")

    return locations[0]["id"]


@tool(args_schema=WeatherInput)
def get_weather(
    location: str,
    units: str = "celsius",
    include_forecast: bool = False,
) -> str:
    """查询真实天气。用户问当前天气查实时天气，用户问明天或预报时查每日天气预报。"""
    unit = _unit(units)
    unit_label = "F" if units == "fahrenheit" else "C"
    location_id = _resolve_location(location)

    if include_forecast:
        data = _request(
            "/v7/weather/3d",
            {
                "location": location_id,
                "unit": unit,
                "lang": "zh",
            },
        )

        daily = data.get("daily") or []
        if len(daily) < 2:
            raise RuntimeError(f"没有拿到明天天气数据：{data}")

        tomorrow = daily[1]
        return (
            f"{location}明天天气："
            f"白天{tomorrow['textDay']}，夜间{tomorrow['textNight']}，"
            f"{tomorrow['tempMin']}°{unit_label} 到 {tomorrow['tempMax']}°{unit_label}，"
            f"{tomorrow['windDirDay']} {tomorrow['windScaleDay']}级，"
            f"湿度{tomorrow['humidity']}%，降水量{tomorrow['precip']}mm。"
        )

    data = _request(
        "/v7/weather/now",
        {
            "location": location_id,
            "unit": unit,
            "lang": "zh",
        },
    )

    now = data["now"]
    return (
        f"{location}当前天气："
        f"{now['text']}，{now['temp']}°{unit_label}，"
        f"体感{now['feelsLike']}°{unit_label}，"
        f"{now['windDir']} {now['windScale']}级，"
        f"湿度{now['humidity']}%，能见度{now['vis']}公里。"
    )