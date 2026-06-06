from langchain.tools import tool
from pydantic import BaseModel, Field

from day1.sandbox.registry import get_sandbox_session, stop_sandbox_session


class SandboxRunInput(BaseModel):
    command: str = Field(description="要在 sandbox 中执行的命令")
    cwd: str = Field(default=".", description="sandbox 内工作目录")
    timeout: int = Field(default=60, ge=1, le=600, description="命令超时时间，单位秒")


class SandboxReadFileInput(BaseModel):
    path: str = Field(description="sandbox 内文件路径")


class SandboxWriteFileInput(BaseModel):
    path: str = Field(description="sandbox 内文件路径")
    content: str = Field(description="要写入的文件内容")


@tool(args_schema=SandboxRunInput)
def sandbox_run(command: str, cwd: str = ".", timeout: int = 60) -> str:
    """在远程 sandbox 中执行命令。适合运行不信任代码、安装临时依赖、测试脚本。"""
    return get_sandbox_session().run(command, cwd=cwd, timeout=timeout)


@tool(args_schema=SandboxReadFileInput)
def sandbox_read_file(path: str) -> str:
    """读取远程 sandbox 中的文本文件。"""
    return get_sandbox_session().read_file(path)


@tool(args_schema=SandboxWriteFileInput)
def sandbox_write_file(path: str, content: str) -> str:
    """写入远程 sandbox 中的文本文件。"""
    return get_sandbox_session().write_file(path, content)


@tool
def sandbox_stop() -> str:
    """停止当前远程 sandbox 会话。"""
    return stop_sandbox_session()
