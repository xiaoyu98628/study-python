from daytona import Daytona, DaytonaConfig

from config.config import config


class DaytonaSandboxSession:
    def __init__(self, sandbox):
        self._sandbox = sandbox

    def run(self, command: str, cwd: str = ".", timeout: int = 60) -> str:
        response = self._sandbox.process.exec(command, cwd=cwd, timeout=timeout)
        return f"Exit code: {response.exit_code}\n\n{response.result}"

    def read_file(self, path: str) -> str:
        content = self._sandbox.fs.download_file(path)
        if content is None:
            return ""
        return content.decode("utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> str:
        self._sandbox.fs.upload_file(content.encode("utf-8"), path)
        return f"写入成功：{path}"

    def stop(self) -> str:
        self._sandbox.stop()
        return "sandbox 已停止"


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
        return DaytonaSandboxSession(sandbox)
