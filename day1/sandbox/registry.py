from day1.sandbox.base import SandboxSession
from day1.sandbox.daytona_provider import DaytonaProvider


_session: SandboxSession | None = None


def get_sandbox_session() -> SandboxSession:
    global _session

    if _session is None:
        _session = DaytonaProvider().create()

    return _session


def stop_sandbox_session() -> str:
    global _session

    if _session is None:
        return "没有正在运行的 sandbox"

    result = _session.stop()
    _session = None
    return result
