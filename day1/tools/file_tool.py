from pathlib import Path

from langchain.tools import tool
from pydantic import BaseModel, Field

from paths import BASE_DIR

_ALLOWED_ROOTS = (BASE_DIR.resolve(),)
_BLOCKED_NAMES = {".env"}
_BLOCKED_PARTS = {".git", ".venv", "__pycache__"}
_BLOCKED_RELATIVE_PREFIXES = (
    Path("storage/app/keys"),
)
_MAX_READ_BYTES = 1_000_000


class ListFilesInput(BaseModel):
    path: str = Field(default=".", description="要列出的目录路径，可以是相对路径或允许根目录内的绝对路径")
    recursive: bool = Field(default=False, description="是否递归列出子目录")
    max_results: int = Field(default=200, ge=1, le=1000, description="最多返回多少条结果")


class ReadFileInput(BaseModel):
    path: str = Field(description="要读取的文件路径，可以是相对路径或允许根目录内的绝对路径")
    max_chars: int = Field(default=20000, ge=1000, le=50000, description="最多返回的字符数")


class SearchFilesInput(BaseModel):
    query: str = Field(min_length=1, description="要搜索的文本")
    path: str = Field(default=".", description="要搜索的目录路径，可以是相对路径或允许根目录内的绝对路径")
    max_results: int = Field(default=50, ge=1, le=500, description="最多返回多少条匹配结果")


def _resolve_path(path: str) -> Path:
    raw_path = Path(path).expanduser()
    candidate = raw_path if raw_path.is_absolute() else BASE_DIR / raw_path
    resolved = candidate.resolve()

    if not any(resolved == root or resolved.is_relative_to(root) for root in _ALLOWED_ROOTS):
        raise RuntimeError("路径不在允许访问的目录内")

    _ensure_allowed_path(resolved)
    return resolved


def _ensure_allowed_path(path: Path) -> None:
    relative_path = _relative_path(path)
    if path.name in _BLOCKED_NAMES:
        raise RuntimeError("出于安全原因，不能访问该文件")

    if any(part in _BLOCKED_PARTS for part in relative_path.parts):
        raise RuntimeError("出于安全原因，不能访问该路径")

    if any(
        relative_path == prefix or relative_path.is_relative_to(prefix)
        for prefix in _BLOCKED_RELATIVE_PREFIXES
    ):
        raise RuntimeError("出于安全原因，不能访问密钥目录")


def _relative_path(path: Path) -> Path:
    for root in _ALLOWED_ROOTS:
        if path == root or path.is_relative_to(root):
            return path.relative_to(root)
    return path


def _display_path(path: Path) -> str:
    relative_path = _relative_path(path)
    return "." if str(relative_path) == "." else str(relative_path)


def _iter_files(directory: Path, recursive: bool):
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    for path in sorted(iterator, key=lambda item: str(_relative_path(item))):
        try:
            _ensure_allowed_path(path)
        except RuntimeError:
            continue
        yield path


def _is_probably_binary(path: Path) -> bool:
    with path.open("rb") as file:
        sample = file.read(4096)
    return b"\x00" in sample


@tool(args_schema=ListFilesInput)
def list_files(path: str = ".", recursive: bool = False, max_results: int = 200) -> str:
    """列出允许访问目录中的文件和子目录。只能访问配置允许的根目录内路径。"""
    directory = _resolve_path(path)
    if not directory.exists():
        raise RuntimeError(f"路径不存在：{path}")
    if not directory.is_dir():
        raise RuntimeError(f"路径不是目录：{path}")

    lines = []
    truncated = False
    for item in _iter_files(directory, recursive):
        kind = "dir" if item.is_dir() else "file"
        lines.append(f"{kind}\t{_display_path(item)}")
        if len(lines) >= max_results:
            truncated = True
            break

    if not lines:
        return f"目录为空：{_display_path(directory)}"

    suffix = f"\n\n结果已截断到 {max_results} 条。" if truncated else ""
    return "\n".join(lines) + suffix


@tool(args_schema=ReadFileInput)
def read_file(path: str, max_chars: int = 20000) -> str:
    """读取允许访问目录中的文本文件。不能读取密钥、.env、.git 等敏感路径。"""
    file_path = _resolve_path(path)
    if not file_path.exists():
        raise RuntimeError(f"文件不存在：{path}")
    if not file_path.is_file():
        raise RuntimeError(f"路径不是文件：{path}")
    if file_path.stat().st_size > _MAX_READ_BYTES:
        raise RuntimeError(f"文件过大，超过 {_MAX_READ_BYTES} 字节")
    if _is_probably_binary(file_path):
        raise RuntimeError("暂不支持读取二进制文件")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars].rstrip()

    suffix = f"\n\n内容已截断到 {max_chars} 字符。" if truncated else ""
    return f"Path: {_display_path(file_path)}\n\n{content}{suffix}"


@tool(args_schema=SearchFilesInput)
def search_files(query: str, path: str = ".", max_results: int = 50) -> str:
    """在允许访问目录中的文本文件里搜索文本。不能搜索密钥、.env、.git 等敏感路径。"""
    directory = _resolve_path(path)
    if not directory.exists():
        raise RuntimeError(f"路径不存在：{path}")
    if not directory.is_dir():
        raise RuntimeError(f"路径不是目录：{path}")

    matches = []
    for file_path in _iter_files(directory, recursive=True):
        if not file_path.is_file():
            continue
        if file_path.stat().st_size > _MAX_READ_BYTES or _is_probably_binary(file_path):
            continue

        with file_path.open("r", encoding="utf-8", errors="replace") as file:
            for line_number, line in enumerate(file, start=1):
                if query in line:
                    text = line.strip()
                    matches.append(f"{_display_path(file_path)}:{line_number}: {text}")
                    if len(matches) >= max_results:
                        return "\n".join(matches) + f"\n\n结果已截断到 {max_results} 条。"

    if not matches:
        return "没有找到匹配结果。"

    return "\n".join(matches)
