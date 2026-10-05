@echo off
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
"%~dp0.env_server\Scripts\python.exe" -m chimera_exam_server.server_cli
