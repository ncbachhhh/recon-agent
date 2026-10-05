"""Scope regression tests must never resolve or contact their fixture targets."""

import socket
from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def block_scope_network(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "socket",
        "create_connection",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
    ):
        monkeypatch.setattr(
            socket,
            name,
            Mock(side_effect=AssertionError("scope tests require no network")),
        )
