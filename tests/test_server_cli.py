import os
import unittest
from unittest.mock import patch

from chimera_exam_server import main, server_cli


class ServerCliTests(unittest.TestCase):
    @patch("chimera_exam_server.main.uvicorn.run")
    def test_main_module_launcher_uses_default_configuration(self, run):
        with patch.dict(os.environ, {}, clear=True):
            main.run_server()

        run.assert_called_once_with(
            main.app,
            host="0.0.0.0",
            port=8000,
            timeout_keep_alive=15,
            access_log=False,
            log_level="info",
        )

    @patch("chimera_exam_server.main.uvicorn.run")
    def test_main_module_launcher_honors_environment_overrides(self, run):
        environment = {
            "CHIMERA_HOST": "127.0.0.1",
            "CHIMERA_PORT": "9000",
            "CHIMERA_UVICORN_LOG_LEVEL": "debug",
        }
        with patch.dict(os.environ, environment, clear=True):
            main.run_server()

        run.assert_called_once_with(
            main.app,
            host="127.0.0.1",
            port=9000,
            timeout_keep_alive=15,
            access_log=False,
            log_level="debug",
        )

    @patch("chimera_exam_server.server_cli.uvicorn.run")
    def test_default_listener_configuration(self, run):
        with patch.dict(os.environ, {}, clear=True):
            server_cli.main()

        run.assert_called_once_with(
            "chimera_exam_server.main:app",
            host="0.0.0.0",
            port=8000,
            timeout_keep_alive=15,
            access_log=False,
            log_level="info",
        )

    @patch("chimera_exam_server.server_cli.uvicorn.run")
    def test_environment_overrides(self, run):
        environment = {
            "CHIMERA_HOST": "127.0.0.1",
            "CHIMERA_PORT": "9000",
            "CHIMERA_UVICORN_LOG_LEVEL": "debug",
        }
        with patch.dict(os.environ, environment, clear=True):
            server_cli.main()

        run.assert_called_once_with(
            "chimera_exam_server.main:app",
            host="127.0.0.1",
            port=9000,
            timeout_keep_alive=15,
            access_log=False,
            log_level="debug",
        )


if __name__ == "__main__":
    unittest.main()
