import asyncio
import os
import threading
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from chimera_exam_server.discovery import (
    SERVER_URL_ENV,
    ZeroconfAdvertiser,
    discover_server,
)


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    @patch("chimera_exam_server.discovery.AsyncZeroconf")
    @patch(
        "chimera_exam_server.discovery._local_ipv4_addresses",
        return_value=[b"\x7f\x00\x00\x01"],
    )
    async def test_advertiser_lifecycle_is_async(self, _addresses, async_zeroconf):
        zeroconf = MagicMock()
        registration_started = asyncio.Event()
        allow_registration = asyncio.Event()

        async def register_service(*_args, **_kwargs):
            registration_started.set()
            await allow_registration.wait()

        zeroconf.async_register_service = AsyncMock(side_effect=register_service)
        zeroconf.async_unregister_service = AsyncMock()
        zeroconf.async_close = AsyncMock()
        async_zeroconf.return_value = zeroconf
        advertiser = ZeroconfAdvertiser()

        start_task = asyncio.create_task(advertiser.start())
        await asyncio.wait_for(registration_started.wait(), timeout=0.1)
        self.assertFalse(start_task.done())
        allow_registration.set()
        await start_task
        await advertiser.stop()

        zeroconf.async_register_service.assert_awaited_once()
        zeroconf.async_unregister_service.assert_awaited_once()
        zeroconf.async_close.assert_awaited_once()

    @patch.dict(os.environ, {SERVER_URL_ENV: "http://exam-server:8000/"})
    async def test_verified_configured_url_is_fallback(self):
        self.assertEqual(
            await discover_server(
                verify=lambda url: url == "http://exam-server:8000"
            ),
            "http://exam-server:8000",
        )

    @patch.dict(os.environ, {SERVER_URL_ENV: "http://wrong-server:8000"})
    async def test_unverified_configured_url_is_rejected(self):
        with self.assertRaises(ConnectionError):
            await discover_server(verify=lambda _url: False)

    @patch.dict(os.environ, {SERVER_URL_ENV: "http://exam-server:8000"})
    async def test_verification_does_not_block_event_loop(self):
        loop_thread = threading.get_ident()
        loop_advanced = False

        def slow_verify(_url: str) -> bool:
            self.assertNotEqual(threading.get_ident(), loop_thread)
            time.sleep(0.05)
            return True

        task = asyncio.create_task(discover_server(verify=slow_verify))
        await asyncio.sleep(0.01)
        loop_advanced = True

        self.assertEqual(await task, "http://exam-server:8000")
        self.assertTrue(loop_advanced)


if __name__ == "__main__":
    unittest.main()