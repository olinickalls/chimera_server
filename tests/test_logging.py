import asyncio
import logging
import os
import re
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from loguru import logger

from chimera_exam_server import logsystem, main
from chimera_exam_server.logsystem import handle_unhandled_exception


class LoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_session_validation_logs_payload_and_errors(self):
        payload = {"username": "candidate"}
        raw_body = b'{"username":"candidate"}'
        errors = [
            {
                "type": "missing",
                "loc": ("body", "set_name"),
                "msg": "Field required",
                "input": payload,
            }
        ]

        async def receive():
            return {"type": "http.request", "body": raw_body, "more_body": False}

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/session/new/",
                "headers": [(b"content-type", b"application/json")],
                "client": ("127.0.0.1", 1234),
                "scheme": "http",
                "server": ("test", 80),
                "query_string": b"",
            },
            receive,
        )
        validation_error = RequestValidationError(errors, body=payload)

        with patch.object(main.logger, "warning") as warning:
            response = await main.request_validation_error(request, validation_error)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.body,
            b'{"detail":[{"type":"missing","loc":["body","set_name"],'
            b'"msg":"Field required","input":{"username":"candidate"}}]}',
        )
        warning.assert_called_once()
        self.assertEqual(warning.call_args.kwargs["payload"], payload)
        self.assertEqual(warning.call_args.kwargs["errors"], errors)

    async def test_lifespan_and_request_context(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            terminal_output = StringIO()
            with (
                patch.dict(os.environ, {"CHIMERA_LOG_DIR": temp_directory}),
                patch.object(
                    main,
                    "ZeroconfAdvertiser",
                    return_value=AsyncMock(),
                ),
                patch.object(logsystem.sys, "stderr", terminal_output),
            ):
                async with main.lifespan(main.app):
                    request = Request(
                        {
                            "type": "http",
                            "method": "GET",
                            "path": "/health",
                            "headers": [
                                (b"x-request-id", b"forged\r\nrequest=attacker")
                            ],
                            "client": ("127.0.0.1", 1234),
                            "scheme": "http",
                            "server": ("test", 80),
                            "query_string": b"",
                        }
                    )
                    response = await main.log_request(
                        request,
                        lambda _request: asyncio.sleep(
                            0, result=Response(status_code=204)
                        ),
                    )

                    self.assertEqual(response.status_code, 204)
                    self.assertTrue(response.headers["X-Request-ID"])
                    self.assertRegex(
                        response.headers["X-Request-ID"], r"^[a-f0-9]{12}$"
                    )
                    self.assertIsNotNone(main.db)

                    async def raise_unexpected_error(_request):
                        raise RuntimeError("unexpected route error")

                    with self.assertRaisesRegex(
                        RuntimeError, "unexpected route error"
                    ):
                        await main.log_request(request, raise_unexpected_error)

                    logging.getLogger("uvicorn.error").warning(
                        "Forwarded Uvicorn record"
                    )
                    logging.getLogger("uvicorn.access").info(
                        "Duplicate access record"
                    )
                    try:
                        raise ValueError("test failure")
                    except ValueError:
                        handle_unhandled_exception(*sys.exc_info())
                        logging.getLogger("uvicorn.error").exception(
                            "Exception in ASGI application"
                        )

                await logger.complete()
                logger.remove()
                log_text = (Path(temp_directory) / "chimera.log").read_text(
                    encoding="utf-8"
                )
                self.assertIn("Request started", log_text)
                self.assertIn("Request complete", log_text)
                self.assertIn("Request failed", log_text)
                self.assertIn("RuntimeError: unexpected route error", log_text)
                self.assertIn("client=127.0.0.1", log_text)
                self.assertIn("status=204", log_text)
                self.assertIn("Forwarded Uvicorn record", log_text)
                self.assertIn("uvicorn.error - Forwarded Uvicorn record", log_text)
                self.assertNotIn("Duplicate access record", log_text)
                self.assertNotIn("Exception in ASGI application", log_text)
                self.assertIn("ValueError: test failure", log_text)
                self.assertIn("\x1b[32mINFO", terminal_output.getvalue())

                started_id = re.search(
                    r"request=([a-f0-9]+).*Request started", log_text
                ).group(1)
                completed_id = re.search(
                    r"request=([a-f0-9]+).*Request complete", log_text
                ).group(1)
                self.assertEqual(started_id, completed_id)

if __name__ == "__main__":
    unittest.main()
