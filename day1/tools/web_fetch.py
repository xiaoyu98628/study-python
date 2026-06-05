import ipaddress
import socket
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup
from langchain.tools import tool
from pydantic import BaseModel, Field


class FetchUrlInput(BaseModel):
    url: str = Field(description="需要读取的网页 URL，必须是 http 或 https")
    max_chars: int = Field(default=5000, ge=500, le=12000, description="返回正文的最大字符数")


def _validate_public_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise RuntimeError("只支持 http 或 https URL")
    if not parsed.hostname:
        raise RuntimeError("URL 缺少主机名")

    hostname = parsed.hostname.lower()
    if hostname in {"localhost"}:
        raise RuntimeError("不允许访问 localhost")

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise RuntimeError(f"无法解析域名：{hostname}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise RuntimeError(f"不允许访问内网或本机地址：{ip}")

    return parsed.geturl()


def _fallback_extract(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    return title, "\n".join(lines)


@tool(args_schema=FetchUrlInput)
def fetch_url(url: str, max_chars: int = 5000) -> str:
    """读取指定网页内容。用户提供 URL 并要求总结、分析或阅读网页时使用。"""
    safe_url = _validate_public_url(url)
    response = requests.get(
        safe_url,
        timeout=15,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Accept": "text/html,text/plain,application/xhtml+xml",
        },
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if not any(kind in content_type for kind in ("text/html", "text/plain", "application/xhtml+xml")):
        raise RuntimeError(f"暂不支持读取该内容类型：{content_type or 'unknown'}")

    title = ""
    extracted = trafilatura.extract(response.text, url=response.url, include_comments=False, include_tables=False)
    if not extracted:
        title, extracted = _fallback_extract(response.text)
    else:
        title, _ = _fallback_extract(response.text)

    if not extracted:
        raise RuntimeError("没有提取到可读正文")

    body = extracted[:max_chars]
    truncated = len(extracted) > max_chars

    return (
        f"网页标题：{title or '未获取到标题'}\n"
        f"最终URL：{response.url}\n"
        f"正文长度：{len(extracted)} 字符\n"
        f"是否截断：{'是' if truncated else '否'}\n\n"
        f"正文：\n{body}"
    )
