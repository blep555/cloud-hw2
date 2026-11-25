"""File-based FIFO queue with inter-process locking."""

import fcntl
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")

    with lock_path.open("a") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _read_names(path: Path) -> list[str]:
    try:
        with path.open(encoding="utf-8") as file:
            return [line.rstrip("\n") for line in file]
    except FileNotFoundError:
        return []


def _write_names(path: Path, names: list[str]) -> None:
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            for name in names:
                file.write(name + "\n")

        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def join(path: str | Path, name: str) -> int:
    if not isinstance(name, str):
        raise ValueError("Invalid name")  # noqa: TRY004 - Queue validation contract

    cleaned_name = name.strip()

    if (
        not cleaned_name
        or len(cleaned_name) > 40
        or "\n" in name
        or "\r" in name
    ):
        raise ValueError("Invalid name")

    path = Path(path)

    with _locked(path):
        names = _read_names(path)
        names.append(cleaned_name)
        _write_names(path, names)
        return len(names)


def take(path: str | Path) -> str:
    path = Path(path)

    with _locked(path):
        names = _read_names(path)

        if not names:
            raise LookupError("empty")

        first_name = names.pop(0)
        _write_names(path, names)
        return first_name
