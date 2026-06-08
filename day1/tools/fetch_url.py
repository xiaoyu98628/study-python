import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from langchain.tools import tool
from pydantic import BaseModel, Field
from readability import Document


class FetchUrlInput(BaseModel):
    url: str = Field(description="要读取的 URL，必须是 http 或 https")
    max_chars: int = Field(default=6000, ge=1000, le=20000, description="最多返回的字符数")


_BLOCKED_HOSTS = {"localhost"}
_MAX_REDIRECTS = 5


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        return _is_blocked_ip(ip.ipv4_mapped)
    return not ip.is_global


def _validate_hostname(hostname: str) -> None:
    normalized = hostname.strip().lower().rstrip(".")
    if not normalized:
        raise RuntimeError("URL 缺少有效主机名")

    if normalized in _BLOCKED_HOSTS or normalized.endswith(".localhost"):
        raise RuntimeError("出于安全原因，不能抓取 localhost 或本机地址")

    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        try:
            addresses = socket.getaddrinfo(normalized, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise RuntimeError(f"无法解析 URL 主机名：{hostname}") from exc

        resolved_ips = {item[4][0] for item in addresses}
        if not resolved_ips:
            raise RuntimeError(f"无法解析 URL 主机名：{hostname}")

        for resolved_ip in resolved_ips:
            if _is_blocked_ip(ipaddress.ip_address(resolved_ip)):
                raise RuntimeError("出于安全原因，不能抓取解析到内网或本机地址的 URL")
        return

    if _is_blocked_ip(ip):
        raise RuntimeError("出于安全原因，不能抓取内网、本机或保留地址")


def _validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("URL 必须是完整的 http 或 https 地址")
    if parsed.username or parsed.password:
        raise RuntimeError("URL 不支持包含用户名或密码")
    if parsed.hostname is None:
        raise RuntimeError("URL 缺少有效主机名")
    _validate_hostname(parsed.hostname)
    return parsed.geturl()


def _get_with_safe_redirects(client: httpx.Client, url: str) -> httpx.Response:
    current_url = _validate_url(url)
    for _ in range(_MAX_REDIRECTS + 1):
        response = client.get(current_url)
        if not response.is_redirect:
            return response

        location = response.headers.get("location")
        if not location:
            return response

        current_url = _validate_url(str(urljoin(str(response.url), location)))

    raise RuntimeError(f"重定向次数超过上限：{_MAX_REDIRECTS}")


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _content_type(headers: httpx.Headers) -> str:
    return headers.get("content-type", "").split(";", 1)[0].strip().lower()


def _truncate(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip(), True


def _soup_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()
    return _normalize_whitespace(soup.get_text(separator="\n"))


def _extract_html(html: str, url: str = "") -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    fallback_title = _normalize_whitespace(soup.title.get_text()) if soup.title else ""
    fallback_content = _soup_text(html)

    try:
        document = Document(html)
        title = _normalize_whitespace(document.short_title() or fallback_title)
    except Exception:
        title = fallback_title

    try:
        content = trafilatura.extract(
            html,
            url=url or None,
            include_comments=False,
            include_tables=False,
        )
    except Exception:
        content = None

    if content:
        return title, _normalize_whitespace(content)

    try:
        document = Document(html)
        content = _soup_text(document.summary(html_partial=True))
    except Exception:
        content = fallback_content

    if not content:
        content = fallback_content

    return title, content


@tool(args_schema=FetchUrlInput)
def fetch_url(url: str, max_chars: int = 6000) -> str:
    """抓取指定 URL 的内容，适合读取已知网页、纯文本或接口返回；不用于搜索未知网页。"""
    normalized_url = _validate_url(url)

    with httpx.Client(
        timeout=10,
        follow_redirects=False,
        headers={
            "User-Agent": "study-python/0.1 fetch_url",
            "Accept": "text/html,application/json,text/plain,application/xml,text/xml;q=0.9,*/*;q=0.8",
        },
    ) as client:
        response = _get_with_safe_redirects(client, normalized_url)

    response.raise_for_status()

    content_type = _content_type(response.headers)
    title = ""

    if content_type in {"text/html", "application/xhtml+xml"}:
        title, content = _extract_html(response.text, str(response.url))
    elif (
        content_type.startswith("text/")
        or content_type in {"application/json", "application/xml", "text/xml"}
    ):
        content = _normalize_whitespace(response.text)
    else:
        return (
            f"URL: {response.url}\n"
            f"Content-Type: {content_type or 'unknown'}\n\n"
            "暂不支持读取该内容类型。"
        )

    if not content:
        return (
            f"URL: {response.url}\n"
            f"Title: {title or '无'}\n"
            f"Content-Type: {content_type or 'unknown'}\n\n"
            "没有提取到可读文本内容。"
        )

    content, truncated = _truncate(content, max_chars)
    suffix = f"\n\n内容已截断到 {max_chars} 字符。" if truncated else ""

    return (
        f"URL: {response.url}\n"
        f"Title: {title or '无'}\n"
        f"Content-Type: {content_type or 'unknown'}\n\n"
        f"内容:\n{content}"
        f"{suffix}"
    )
