from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Any, Self


class LockUnavailableError(RuntimeError):
    """Raised when an exclusive lock cannot be acquired."""


class FileLock:
    """Cross-platform exclusive lock backed by a separate lock file."""

    def __init__(
        self,
        path: str | Path,
        *,
        blocking: bool = True,
    ) -> None:
        self._path = Path(path)
        self._blocking = blocking
        self._stream: Any = None

    def acquire(self) -> None:
        """Acquire the exclusive lock."""

        if self._stream is not None:
            raise RuntimeError("Lock is already acquired.")

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        stream = self._path.open("a+b")

        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\0")
            stream.flush()

        stream.seek(0)

        try:
            if sys.platform == "win32":
                import msvcrt

                if self._blocking:
                    mode = msvcrt.LK_LOCK
                else:
                    mode = msvcrt.LK_NBLCK

                msvcrt.locking(
                    stream.fileno(),
                    mode,
                    1,
                )
            else:
                import fcntl

                if self._blocking:
                    operation = fcntl.LOCK_EX
                else:
                    operation = fcntl.LOCK_EX | fcntl.LOCK_NB

                fcntl.flock(
                    stream.fileno(),
                    operation,
                )

        except (OSError, BlockingIOError) as exc:
            stream.close()

            if self._blocking:
                raise

            raise LockUnavailableError(f"Unable to acquire lock: {self._path}") from exc

        self._stream = stream

    def release(self) -> None:
        """Release the exclusive lock."""

        if self._stream is None:
            return

        stream = self._stream

        try:
            if sys.platform == "win32":
                import msvcrt

                stream.seek(0)
                msvcrt.locking(
                    stream.fileno(),
                    msvcrt.LK_UNLCK,
                    1,
                )
            else:
                import fcntl

                fcntl.flock(
                    stream.fileno(),
                    fcntl.LOCK_UN,
                )
        finally:
            stream.close()
            self._stream = None

    def __enter__(self) -> Self:
        """Acquire the lock for a context-managed operation."""

        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        """Release the lock when leaving the context."""

        del exc_type, exc_value, traceback
        self.release()
