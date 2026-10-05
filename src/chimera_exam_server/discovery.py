"""Zeroconf discovery for the Chimera exam server."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import socket
from collections.abc import Callable
from urllib.error import URLError
from urllib.request import urlopen

from zeroconf import IPVersion, ServiceInfo, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf


DEFAULT_HTTP_PORT = 8000
DISCOVERY_MAGIC = "chimera-exam-server"
DISCOVERY_VERSION = 1
SERVICE_TYPE = "_chimera-exam._tcp.local."
SERVER_URL_ENV = "CHIMERA_SERVER_URL"


def _local_ipv4_addresses() -> list[bytes]:
    addresses: set[str] = set()
    try:
        for result in socket.getaddrinfo(
            socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM
        ):
            addresses.add(result[4][0])
    except socket.gaierror:
        pass

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("224.0.0.251", 5353))
        addresses.add(probe.getsockname()[0])
    except OSError:
        pass
    finally:
        probe.close()

    usable = sorted(
        address
        for address in addresses
        if not ipaddress.ip_address(address).is_loopback and address != "0.0.0.0"
    )
    if not usable:
        raise RuntimeError("No LAN IPv4 address is available for Zeroconf")
    return [socket.inet_aton(address) for address in usable]


class ZeroconfAdvertiser:
    def __init__(self, http_port: int = DEFAULT_HTTP_PORT) -> None:
        hostname = socket.gethostname()
        self._zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
        self._service = ServiceInfo(
            type_=SERVICE_TYPE,
            name=f"Chimera Exam Server on {hostname}.{SERVICE_TYPE}",
            addresses=_local_ipv4_addresses(),
            port=http_port,
            properties={
                "path": "/discovery/identity",
                "version": str(DISCOVERY_VERSION),
            },
            server=f"{hostname}.local.",
        )
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        await self._zeroconf.async_register_service(
            self._service,
            allow_name_change=True,
        )
        self._started = True

    async def stop(self) -> None:
        if self._started:
            await self._zeroconf.async_unregister_service(self._service)
            self._started = False
        await self._zeroconf.async_close()


def verify_server(url: str, timeout: float = 1.5) -> bool:
    try:
        with urlopen(f"{url.rstrip('/')}/discovery/identity", timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, URLError, ValueError):
        return False
    return isinstance(payload, dict) and (
        response.status == 200
        and payload.get("service") == DISCOVERY_MAGIC
        and payload.get("version") == DISCOVERY_VERSION
    )


async def discover_server(
    timeout: float = 4.0,
    verify: Callable[[str], bool] = verify_server,
) -> str:
    """Find and verify a server without blocking the caller's event loop."""
    configured_url = os.environ.get(SERVER_URL_ENV)
    if configured_url:
        configured_url = configured_url.rstrip("/")
        if await asyncio.to_thread(verify, configured_url):
            return configured_url
        raise ConnectionError(f"{SERVER_URL_ENV} does not identify a Chimera server")

    loop = asyncio.get_running_loop()
    names: asyncio.Queue[str] = asyncio.Queue()

    def on_service_state_change(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        del zeroconf, service_type
        if state_change in (ServiceStateChange.Added, ServiceStateChange.Updated):
            loop.call_soon_threadsafe(names.put_nowait, name)

    async_zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
    browser = AsyncServiceBrowser(
        async_zeroconf.zeroconf,
        SERVICE_TYPE,
        handlers=[on_service_state_change],
    )
    deadline = loop.time() + timeout

    try:
        while (remaining := deadline - loop.time()) > 0:
            try:
                name = await asyncio.wait_for(names.get(), timeout=remaining)
            except TimeoutError:
                break

            info = await async_zeroconf.async_get_service_info(
                SERVICE_TYPE,
                name,
                timeout=min(1000, max(1, int((deadline - loop.time()) * 1000))),
            )
            if info is None:
                continue
            for address in info.parsed_addresses(IPVersion.V4Only):
                url = f"http://{address}:{info.port}"
                if await asyncio.to_thread(verify, url):
                    return url
    finally:
        await browser.async_cancel()
        await async_zeroconf.async_close()

    raise ConnectionError(
        "Chimera server not found on this LAN. "
        f"Set {SERVER_URL_ENV}=http://<server-hostname-or-ip>:8000 as a fallback."
    )