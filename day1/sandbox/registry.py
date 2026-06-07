from day1.sandbox.base import SandboxSession
from day1.sandbox.daytona_provider import DaytonaProvider
from day1.sandbox.docker_provider import DockerProvider
from config.config import config


_session: SandboxSession | None = None


def _create_provider():
    provider = config().sandbox.sandbox_provider
    if provider == "daytona":
        return DaytonaProvider()
    if provider == "docker":
        return DockerProvider()
    raise RuntimeError(f"不支持的 sandbox provider：{provider}")


def get_sandbox_session() -> SandboxSession:
    global _session

    if _session is None:
        _session = _create_provider().create()

    return _session


def stop_sandbox_session() -> str:
    if _session is None:
        return "没有正在运行的 sandbox"

    return _session.stop()


def sandbox_session_status() -> str:
    if _session is None:
        return "没有正在运行的 sandbox"

    return _session.status()


def delete_sandbox_session() -> str:
    global _session

    if _session is None:
        return "没有正在运行的 sandbox"

    try:
        return _session.delete()
    finally:
        _session = None


def cleanup_sandbox_session() -> str:
    global _session

    if _session is None:
        return "没有正在运行的 sandbox"

    try:
        return _session.stop_and_delete()
    finally:
        _session = None
