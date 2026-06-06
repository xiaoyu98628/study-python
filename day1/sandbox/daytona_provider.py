from daytona import Daytona, DaytonaConfig

from config.config import config
from day1.sandbox.logging import sandbox_logger


class DaytonaSandboxSession:
    provider = "daytona"

    def __init__(self, sandbox):
        self._sandbox = sandbox

    @property
    def id(self) -> str:
        return str(getattr(self._sandbox, "id", "unknown"))

    def status(self) -> str:
        state = getattr(self._sandbox, "state", "unknown")
        desired_state = getattr(self._sandbox, "desired_state", "unknown")
        created_at = getattr(self._sandbox, "created_at", "unknown")
        return (
            "当前 sandbox：\n"
            f"provider: {self.provider}\n"
            f"id: {self.id}\n"
            f"state: {state}\n"
            f"desired_state: {desired_state}\n"
            f"created_at: {created_at}"
        )

    def run(self, command: str, cwd: str = ".", timeout: int = 60) -> str:
        sandbox_logger.debug("sandbox_run id=%r command=%r cwd=%r timeout=%r", self.id, command, cwd, timeout)
        response = self._sandbox.process.exec(command, cwd=cwd, timeout=timeout)
        sandbox_logger.debug("sandbox_run_result id=%r exit_code=%r", self.id, response.exit_code)
        return f"Exit code: {response.exit_code}\n\n{response.result}"

    def read_file(self, path: str) -> str:
        sandbox_logger.debug("sandbox_read_file id=%r path=%r", self.id, path)
        content = self._sandbox.fs.download_file(path)
        if content is None:
            return ""
        return content.decode("utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> str:
        sandbox_logger.debug("sandbox_write_file id=%r path=%r chars=%r", self.id, path, len(content))
        self._sandbox.fs.upload_file(content.encode("utf-8"), path)
        return f"写入成功：{path}"

    def stop(self) -> str:
        sandbox_logger.debug("sandbox_stop id=%r", self.id)
        self._sandbox.stop()
        sandbox_logger.debug("sandbox_stopped id=%r", self.id)
        return "sandbox 已停止"

    def delete(self) -> str:
        sandbox_logger.debug("sandbox_delete id=%r", self.id)
        self._sandbox.delete()
        sandbox_logger.debug("sandbox_deleted id=%r", self.id)
        return "sandbox 已删除"

    def stop_and_delete(self) -> str:
        errors = []

        try:
            sandbox_logger.debug("sandbox_cleanup_stop id=%r", self.id)
            self._sandbox.stop()
        except Exception as exc:
            errors.append(f"stop 失败：{exc}")
            sandbox_logger.exception("sandbox_cleanup_stop_failed id=%r", self.id)

        try:
            sandbox_logger.debug("sandbox_cleanup_delete id=%r", self.id)
            self._sandbox.delete()
        except Exception as exc:
            errors.append(f"delete 失败：{exc}")
            sandbox_logger.exception("sandbox_cleanup_delete_failed id=%r", self.id)

        if errors:
            raise RuntimeError("；".join(errors))

        sandbox_logger.debug("sandbox_cleaned_up id=%r", self.id)
        return "sandbox 已停止并删除"


class DaytonaProvider:
    def __init__(self):
        sandbox_config = config().sandbox
        if sandbox_config.sandbox_provider != "daytona":
            raise RuntimeError(f"不支持的 sandbox provider：{sandbox_config.sandbox_provider}")
        if not sandbox_config.daytona_api_key:
            raise RuntimeError("缺少环境变量 DAYTONA_API_KEY")

        self._client = Daytona(
            DaytonaConfig(
                api_key=sandbox_config.daytona_api_key,
                api_url=sandbox_config.daytona_api_url or None,
                target=sandbox_config.daytona_target or None,
            )
        )

    def create(self) -> DaytonaSandboxSession:
        sandbox = self._client.create()
        session = DaytonaSandboxSession(sandbox)
        sandbox_logger.debug("sandbox_created provider=%r id=%r", session.provider, session.id)
        return session
