"""Command-line entry point for the Chimera exam server."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "chimera_exam_server.main:app",
        host=os.getenv("CHIMERA_HOST", "0.0.0.0"),
        port=int(os.getenv("CHIMERA_PORT", "8000")),
        timeout_keep_alive=15,
        access_log=False,
        log_level=os.getenv("CHIMERA_UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
