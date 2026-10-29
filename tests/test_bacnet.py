"""Regression tests for BACnet request cleanup."""

import asyncio
import unittest

from flexit_bacnet.bacnet import BACnetRequest


class BACnetRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_lost_completes_pending_request(self):
        request = BACnetRequest(b"request")

        request.connection_lost(None)

        self.assertTrue(await request.wait(timeout=0))
        self.assertIsNone(request.exception)

    async def test_connection_lost_after_timeout(self):
        request = BACnetRequest(b"request")

        with self.assertRaises(asyncio.TimeoutError):
            await request.wait(timeout=0)

        request.connection_lost(None)

        self.assertTrue(request.done.cancelled())

    async def test_connection_lost_after_waiter_cancelled(self):
        request = BACnetRequest(b"request")
        waiter = asyncio.ensure_future(request.wait())
        asyncio.get_running_loop().call_soon(waiter.cancel)

        with self.assertRaises(asyncio.CancelledError):
            await waiter

        request.connection_lost(None)

        self.assertTrue(request.done.cancelled())

    async def test_connection_lost_after_request_completed(self):
        request = BACnetRequest(b"request")
        request.connection_lost(None)

        request.connection_lost(None)

        self.assertTrue(await request.wait(timeout=0))
