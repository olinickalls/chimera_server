# Offline LAN setup

The HTTP server listens on every network interface. Clients call
the async `discover_server()` coroutine from
`chimera_exam_server.discovery`. Zeroconf
advertises and browses the `_chimera-exam._tcp.local.` DNS-SD service. A
client accepts an endpoint only after checking the Chimera identity endpoint
over HTTP; browsing, resolution, and verification do not block its event loop.

Start discovery as a background task in an async client:

```python
discovery_task = asyncio.create_task(discover_server())
```

Await the task from application workflow code when the URL is needed. Cancel
it when the application exits. A Qt client should bridge this coroutine with
its asyncio integration rather than call `asyncio.run()` on the UI thread.

## Router

- Connect the server by Ethernet and clients by Wi-Fi to the same LAN/VLAN.
- Disable Wi-Fi client/AP isolation. It prevents clients from reaching wired
  LAN devices.
- Enable multicast between wired and Wi-Fi clients. Zeroconf uses mDNS at
  `224.0.0.251` on UDP port 5353.
- The router can use DHCP; no fixed server address is required.
- A DHCP reservation is still a useful operational fallback, but discovery
  does not depend on one.

## Windows firewall

Run these once in an elevated PowerShell terminal on the server:

```powershell
New-NetFirewallRule -DisplayName "Chimera HTTP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -Profile Private
New-NetFirewallRule -DisplayName "Chimera mDNS" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 5353 -Profile Private
```

Ensure Windows classifies the router connection as `Private`, then start the
server with `run_server.bat`.

## Fallback and diagnostics

If the router blocks multicast, set `CHIMERA_SERVER_URL` on clients
to a resolvable server hostname or DHCP-reserved address. The value is still
verified against `/discovery/identity` before use:

```powershell
$env:CHIMERA_SERVER_URL = "http://exam-server:8000"
```

Only one Chimera server should run on a LAN. Discovery retries for four
seconds; applications should show the resulting `ConnectionError` and offer a
Retry action rather than silently continuing offline.

## Logging

Loguru writes console output and `logs/chimera.log` by default. HTTP requests
include a request ID, client address, method, path, status, and duration. Exam
answers, SQL parameters, usernames, UIDs, and environment dumps are excluded.

The file sink is queued so disk writes do not block requests. Files rotate at
10 MB, are retained for 14 days, and old files are compressed with gzip. These
settings can be changed with environment variables:

```text
CHIMERA_LOG_DIR=/var/log/chimera
CHIMERA_LOG_LEVEL=INFO
CHIMERA_LOG_ROTATION=10 MB
CHIMERA_LOG_RETENTION=14 days
```

On Raspberry Pi, create the selected directory and grant it to the account
running the service before startup. For a systemd deployment, set these values
with `Environment=` entries and use `--no-access-log` with Uvicorn because the
application middleware already records richer access logs. Standard Uvicorn
error records are forwarded into Loguru.

## Installation and packaging

Python 3.11 or newer is required. `pyproject.toml` is the canonical source for
application metadata and dependencies. `requirements.txt` installs that local
project, so a deployment from a source checkout is:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/chimera-server
```

For development tools and the standalone API test client, install the `dev`
extra (including the standalone API smoke client at
`scripts/api_smoke.py`):

```bash
.venv/bin/python -m pip install ".[dev]"
```

Build a portable wheel with:

```bash
.venv/bin/python -m pip install build
.venv/bin/python -m build
```

Copy the resulting `dist/chimera_exam_server-*.whl` to the Raspberry Pi and
install it into a virtual environment with `pip install <wheel>`. Start it with
`chimera-server`. The command listens on all IPv4 interfaces by default.

The following optional environment variables configure the listener:

```text
CHIMERA_HOST=0.0.0.0
CHIMERA_PORT=8000
CHIMERA_UVICORN_LOG_LEVEL=info
CHIMERA_DATA_DIR=C:\ChimeraData
```

The database is stored in `DB/` beneath the current working directory by
default. Set `CHIMERA_DATA_DIR` to choose another data directory; reports are
written to `REPORTS/` beneath the current working directory.