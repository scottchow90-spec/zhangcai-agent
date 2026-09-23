"""Optional strict-local Python network policy.

The normal packaged desktop runtime is local-first and supports explicit
on-demand public-source downloads. Those scripts write their responses into
the user resource library before the Harness reads them. This module only
enables a diagnostic strict-local mode when ZHANGCAI_DATA_POLICY is set to
local_tdx_only; packaged mode uses local_first_on_demand instead.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from typing import Any


_POLICY = os.environ.get("ZHANGCAI_DATA_POLICY", "").strip().casefold()


def _is_loopback_host(host: object) -> bool:
    value = str(host or "").strip().strip("[]").casefold()
    if value in {"localhost", "localhost."}:
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _host_from_address(address: object) -> object:
    if isinstance(address, tuple) and address:
        return address[0]
    return address


def _network_blocked(host: object) -> OSError:
    return OSError(
        f"desktop_local_tdx_only_policy: outbound network blocked for {host!s}; "
        "use local data or the selected TDX/Mock directory"
    )


def _install_local_only_policy() -> None:
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def connect(self: socket.socket, address: Any) -> Any:
        host = _host_from_address(address)
        if not _is_loopback_host(host):
            raise _network_blocked(host)
        return original_connect(self, address)

    def connect_ex(self: socket.socket, address: Any) -> int:
        host = _host_from_address(address)
        if not _is_loopback_host(host):
            raise _network_blocked(host)
        return original_connect_ex(self, address)

    def create_connection(address: Any, timeout: Any = socket._GLOBAL_DEFAULT_TIMEOUT, source_address: Any = None) -> Any:
        host = _host_from_address(address)
        if not _is_loopback_host(host):
            raise _network_blocked(host)
        return original_create_connection(address, timeout, source_address)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.create_connection = create_connection


if _POLICY == "local_tdx_only":
    _install_local_only_policy()
