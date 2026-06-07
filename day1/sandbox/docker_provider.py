import shutil
import subprocess
import uuid
from pathlib import Path

from config.config import config
from day1.sandbox.logging import sandbox_logger
from paths import BASE_DIR


SANDBOX_ROOT = BASE_DIR / "storage" / "sandboxes"
CONTAINER_WORKDIR = "/workspace"


class DockerSandboxSession:
    provider = "docker"

    def __init__(self, container_name: str, workspace_dir: Path):
        self._container_name = container_name
        self._workspace_dir = workspace_dir

    @property
    def id(self) -> str:
        return self._container_name

    def status(self) -> str:
        result = self._docker(
            [
                "inspect",
                "--format",
                "{{.State.Status}}|{{.State.Running}}|{{.Created}}|{{.Config.Image}}",
                self.id,
            ],
            check=False,
        )
        if result.returncode != 0:
            return (
                "当前 sandbox：\n"
                f"provider: {self.provider}\n"
                f"id: {self.id}\n"
                "state: missing"
            )

        state, running, created_at, image = result.stdout.strip().split("|", maxsplit=3)
        return (
            "当前 sandbox：\n"
            f"provider: {self.provider}\n"
            f"id: {self.id}\n"
            f"state: {state}\n"
            f"running: {running}\n"
            f"image: {image}\n"
            f"workspace: {self._workspace_dir}\n"
            f"created_at: {created_at}"
        )

    def run(self, command: str, cwd: str = ".", timeout: int = 60) -> str:
        workdir = self._container_cwd(cwd)
        sandbox_logger.debug("sandbox_run id=%r command=%r cwd=%r timeout=%r", self.id, command, workdir, timeout)
        result = self._docker(
            ["exec", "-w", workdir, self.id, "sh", "-lc", command],
            timeout=timeout,
            check=False,
        )
        sandbox_logger.debug("sandbox_run_result id=%r exit_code=%r", self.id, result.returncode)
        output = result.stdout
        if result.stderr:
            output = f"{output}\n{result.stderr}" if output else result.stderr
        return f"Exit code: {result.returncode}\n\n{output}"

    def read_file(self, path: str) -> str:
        file_path = self._workspace_path(path)
        sandbox_logger.debug("sandbox_read_file id=%r path=%r resolved=%r", self.id, path, str(file_path))
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{path}")
        if not file_path.is_file():
            raise IsADirectoryError(f"不是文本文件：{path}")
        return file_path.read_text(encoding="utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> str:
        file_path = self._workspace_path(path)
        sandbox_logger.debug("sandbox_write_file id=%r path=%r resolved=%r chars=%r", self.id, path, str(file_path), len(content))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"写入成功：{path}"

    def stop(self) -> str:
        sandbox_logger.debug("sandbox_stop id=%r", self.id)
        self._docker(["stop", self.id], check=False)
        sandbox_logger.debug("sandbox_stopped id=%r", self.id)
        return "sandbox 已停止"

    def delete(self) -> str:
        sandbox_logger.debug("sandbox_delete id=%r", self.id)
        self._docker(["rm", "-f", self.id], check=False)
        shutil.rmtree(self._workspace_dir, ignore_errors=True)
        sandbox_logger.debug("sandbox_deleted id=%r", self.id)
        return "sandbox 已删除"

    def stop_and_delete(self) -> str:
        errors = []

        try:
            self.stop()
        except Exception as exc:
            errors.append(f"stop 失败：{exc}")
            sandbox_logger.exception("sandbox_cleanup_stop_failed id=%r", self.id)

        try:
            self.delete()
        except Exception as exc:
            errors.append(f"delete 失败：{exc}")
            sandbox_logger.exception("sandbox_cleanup_delete_failed id=%r", self.id)

        if errors:
            raise RuntimeError("；".join(errors))

        sandbox_logger.debug("sandbox_cleaned_up id=%r", self.id)
        return "sandbox 已停止并删除"

    def _container_cwd(self, cwd: str) -> str:
        if not cwd or cwd == ".":
            return CONTAINER_WORKDIR

        raw_path = Path(cwd)
        if raw_path.is_absolute():
            if cwd == CONTAINER_WORKDIR or cwd.startswith(f"{CONTAINER_WORKDIR}/"):
                return cwd
            raise ValueError(f"cwd 必须位于 {CONTAINER_WORKDIR} 内")

        self._workspace_path(cwd)
        return f"{CONTAINER_WORKDIR}/{cwd.strip('/')}"

    def _workspace_path(self, path: str) -> Path:
        if not path:
            raise ValueError("path 不能为空")

        raw_path = Path(path)
        if raw_path.is_absolute():
            path_text = str(raw_path)
            if path_text == CONTAINER_WORKDIR:
                relative_path = Path(".")
            elif path_text.startswith(f"{CONTAINER_WORKDIR}/"):
                relative_path = Path(path_text.removeprefix(f"{CONTAINER_WORKDIR}/"))
            else:
                raise ValueError(f"path 必须位于 {CONTAINER_WORKDIR} 内")
        else:
            relative_path = raw_path

        resolved = (self._workspace_dir / relative_path).resolve()
        workspace = self._workspace_dir.resolve()
        if resolved != workspace and workspace not in resolved.parents:
            raise ValueError("path 不能逃逸 sandbox workspace")
        return resolved

    @staticmethod
    def _docker(args: list[str], timeout: int | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                ["docker", *args],
                capture_output=True,
                check=check,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("未找到 docker 命令，请先安装并启动 Docker") from exc
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise RuntimeError(message) from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"命令执行超时：{timeout}s") from exc

        return result


class DockerProvider:
    def __init__(self):
        sandbox_config = config().sandbox
        if sandbox_config.sandbox_provider != "docker":
            raise RuntimeError(f"不支持的 sandbox provider：{sandbox_config.sandbox_provider}")

        self._image = sandbox_config.docker_image
        self._network = sandbox_config.docker_network
        self._memory = sandbox_config.docker_memory
        self._cpus = sandbox_config.docker_cpus
        self._prefix = sandbox_config.docker_container_prefix

    def create(self) -> DockerSandboxSession:
        if not self._image:
            raise RuntimeError("缺少 Docker sandbox 镜像配置 DOCKER_SANDBOX_IMAGE")

        session_id = uuid.uuid4().hex[:12]
        container_name = f"{self._prefix}{session_id}"
        workspace_dir = SANDBOX_ROOT / session_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        args = [
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            self._network,
            "--workdir",
            CONTAINER_WORKDIR,
            "--user",
            "1000:1000",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,size=128m",
            "--mount",
            f"type=bind,src={workspace_dir},dst={CONTAINER_WORKDIR}",
        ]

        if self._memory:
            args.extend(["--memory", self._memory])
        if self._cpus:
            args.extend(["--cpus", self._cpus])

        args.extend([self._image, "sleep", "infinity"])

        try:
            DockerSandboxSession._docker(args)
        except Exception:
            shutil.rmtree(workspace_dir, ignore_errors=True)
            raise

        session = DockerSandboxSession(container_name, workspace_dir)
        sandbox_logger.debug("sandbox_created provider=%r id=%r image=%r", session.provider, session.id, self._image)
        return session
