from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests.shared.host import Result


@pytest.fixture
def context() -> SimpleNamespace:
    return SimpleNamespace(scenario=SimpleNamespace(skip=Mock()))


@pytest.fixture
def make_result() -> Callable[..., Result]:
    def factory(
        command: str = "probe",
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> Result:
        return Result(
            command=command,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    return factory
