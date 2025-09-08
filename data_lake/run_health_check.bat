@echo off
set PROJECT_ROOT=%~dp0
echo Setting PROJECT_ROOT to %PROJECT_ROOT%
python "%PROJECT_ROOT%src\common\pipeline_health_monitor.py" %*