@echo off
title Disaster Sentinel — Live Node Monitor
cd /d "%~dp0"
python tools\monitor_node.py
pause

