@echo off
title Disaster Sentinel — 4-Port USB Hub Serial Bridge
cd /d "%~dp0"
echo ===================================================
echo   DISASTER SENTINEL - MULTI-NODE SERIAL BRIDGE
echo ===================================================
echo Starting Multi-Node Bridge for 4-Port USB Hub...
python tools\serial_bridge.py
pause

