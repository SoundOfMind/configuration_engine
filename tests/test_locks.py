from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from configuration_engine.locks import (
    FileLock,
    LockUnavailableError,
)


def test_lock_can_be_acquired_and_released(tmp_path: Path) -> None:
    """A lock can be acquired and released."""

    lock_path = tmp_path / "test.lock"
    lock = FileLock(
        lock_path,
        blocking=False,
    )

    lock.acquire()

    assert lock_path.exists()

    lock.release()

    lock.release()


def test_lock_context_manager_releases_lock(tmp_path: Path) -> None:
    """A context-managed lock is released when the context exits."""

    lock_path = tmp_path / "test.lock"

    with FileLock(
        lock_path,
        blocking=False,
    ):
        assert lock_path.exists()

    lock = FileLock(
        lock_path,
        blocking=False,
    )

    lock.acquire()
    lock.release()


def test_nonblocking_lock_fails_when_another_process_holds_lock(
    tmp_path: Path,
) -> None:
    """A non-blocking lock fails when another process owns the lock."""

    lock_path = tmp_path / "test.lock"

    script = """
from pathlib import Path
import sys
import time

from configuration_engine.locks import FileLock

path = Path(sys.argv[1])

with FileLock(path, blocking=False):
    print("LOCKED", flush=True)
    time.sleep(30)
"""

    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "LOCKED"

        lock = FileLock(
            lock_path,
            blocking=False,
        )

        with pytest.raises(LockUnavailableError):
            lock.acquire()

        lock.release()

    finally:
        process.terminate()
        process.wait(timeout=5)


def test_lock_can_be_reacquired_after_release(tmp_path: Path) -> None:
    """A lock can be acquired again after it is released."""

    lock_path = tmp_path / "test.lock"

    first = FileLock(
        lock_path,
        blocking=False,
    )

    first.acquire()
    first.release()

    second = FileLock(
        lock_path,
        blocking=False,
    )

    second.acquire()
    second.release()


def test_lock_releases_after_exception(tmp_path: Path) -> None:
    """A context-managed lock releases when the body raises."""

    lock_path = tmp_path / "test.lock"

    with (
        pytest.raises(RuntimeError),
        FileLock(
            lock_path,
            blocking=False,
        ),
    ):
        raise RuntimeError("test failure")

    lock = FileLock(
        lock_path,
        blocking=False,
    )

    lock.acquire()
    lock.release()


def test_acquiring_same_lock_object_twice_raises(
    tmp_path: Path,
) -> None:
    """A lock object cannot be acquired twice."""

    lock_path = tmp_path / "test.lock"

    lock = FileLock(
        lock_path,
        blocking=False,
    )

    lock.acquire()

    try:
        with pytest.raises(RuntimeError, match="already acquired"):
            lock.acquire()
    finally:
        lock.release()
