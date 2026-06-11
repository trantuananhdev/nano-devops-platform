"""
T-26: Docker Ephemeral Sandbox Executor.

Chạy Python snippets trong ephemeral Docker container với:
  - --network none      → không có egress ra ngoài
  - --memory 64m        → capped RAM
  - --cpus 0.5          → capped CPU
  - --read-only         → filesystem read-only
  - --rm                → auto-remove sau khi xong
  - stdin=DEVNULL, timeout cứng

Fallback về process-level sandbox nếu Docker socket không available
(dev mode, hoặc sandbox_use_docker=False trong config).

NOTE: Cần Docker socket mounted vào worker container:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Max output trả về agent (tránh context overflow)
_MAX_OUTPUT_CHARS = 8_192


class DockerSandboxResult:
    """Result from Docker sandbox execution — mirrors SandboxResult interface."""

    def __init__(
        self,
        *,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool = False,
        error: str | None = None,
        backend: str = "docker",
    ) -> None:
        self.stdout    = stdout
        self.stderr    = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.error     = error
        self.backend   = backend  # "docker" or "process_fallback"

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.error

    def to_agent_dict(self) -> dict[str, Any]:
        return {
            "stdout":    self.stdout[:_MAX_OUTPUT_CHARS] if self.stdout else "",
            "stderr":    self.stderr[:_MAX_OUTPUT_CHARS] if self.stderr else "",
            "exit_code": self.exit_code,
            "success":   self.success,
            "timed_out": self.timed_out,
            "error":     self.error,
            "backend":   self.backend,
            "hint": (
                f"Docker sandbox: thành công (backend={self.backend})." if self.success
                else (
                    f"Docker sandbox: timeout ({get_settings().sandbox_docker_timeout_s}s)."
                    if self.timed_out
                    else f"Docker sandbox: thất bại (exit={self.exit_code}). stderr={self.stderr[:200]}"
                )
            ),
        }


async def _docker_available() -> bool:
    """Quick check: can we call 'docker info'?"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            stdin=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        return proc.returncode == 0
    except Exception:
        return False


async def run_python_in_docker(
    code: str,
    *,
    timeout_s: int | None = None,
) -> DockerSandboxResult:
    """
    Execute Python code inside an ephemeral Docker container.

    Security constraints:
      - --network none: no outbound network
      - --memory / --cpus: resource caps
      - --read-only: immutable filesystem
      - --rm: ephemeral, auto-removed

    Args:
        code:      Python source code string
        timeout_s: Override timeout (default from config)

    Returns:
        DockerSandboxResult with stdout/stderr/exit_code
    """
    cfg = get_settings()
    t   = timeout_s or cfg.sandbox_docker_timeout_s

    if not code or not code.strip():
        return DockerSandboxResult(
            stdout="", stderr="Code rỗng", exit_code=1, error="Empty code",
        )

    # Safety: still block dangerous patterns even in Docker
    dangerous = ["__import__", "eval(", "exec("]
    for pat in dangerous:
        if pat in code:
            return DockerSandboxResult(
                stdout="", stderr=f"Pattern bị cấm: {pat}",
                exit_code=1, error=f"Blocked: {pat}",
            )

    # Escape code for shell -c invocation
    escaped_code = code.replace("'", "'\"'\"'")

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        f"--memory={cfg.sandbox_docker_memory}",
        "--cpus=0.5",
        "--read-only",
        "--tmpfs=/tmp:rw,noexec,size=32m",
        "--user=nobody",
        cfg.sandbox_docker_image,
        "python3", "-c", code,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=float(t)
            )
            return DockerSandboxResult(
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                backend="docker",
            )
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await proc.communicate()
            except Exception:
                pass
            logger.warning("Docker sandbox timeout (%ds) for code snippet", t)
            return DockerSandboxResult(
                stdout="", stderr=f"Docker timeout sau {t}s",
                exit_code=124, timed_out=True, backend="docker",
            )
    except FileNotFoundError:
        logger.warning("docker CLI not found — cannot use Docker sandbox")
        return DockerSandboxResult(
            stdout="", stderr="docker CLI không tìm thấy",
            exit_code=127, error="docker not found", backend="docker",
        )
    except Exception as exc:
        logger.exception("Docker sandbox unexpected error")
        return DockerSandboxResult(
            stdout="", stderr=str(exc),
            exit_code=1, error=str(exc), backend="docker",
        )


class DockerSandboxExecutor:
    """
    High-level executor: routes to Docker if available + configured,
    falls back to process-level sandbox otherwise.

    Usage:
        executor = DockerSandboxExecutor()
        result = await executor.run_python(code)
    """

    async def run_python(
        self,
        code: str,
        *,
        timeout_s: int | None = None,
    ) -> DockerSandboxResult:
        """Run Python code, choosing Docker vs process sandbox based on config."""
        cfg = get_settings()

        if cfg.sandbox_use_docker and await _docker_available():
            logger.debug("DockerSandboxExecutor: using Docker backend")
            return await run_python_in_docker(code, timeout_s=timeout_s)

        # Fallback: process-level sandbox (always available)
        logger.debug("DockerSandboxExecutor: falling back to process sandbox")
        from app.services.tools.sandbox_executor import run_python_snippet
        result = await run_python_snippet(code, timeout_s=timeout_s or cfg.sandbox_docker_timeout_s)
        return DockerSandboxResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            error=result.error,
            backend="process_fallback",
        )


# Module-level singleton
_executor: DockerSandboxExecutor | None = None


def get_docker_executor() -> DockerSandboxExecutor:
    global _executor
    if _executor is None:
        _executor = DockerSandboxExecutor()
    return _executor
