@echo off
pushd "%~dp0..\.."
python -m test_manuals --pdf "Predici11_Workshop_November_2016_1. Presto-Kinetics.pdf" --output "%~dp0"
set EXIT_CODE=%ERRORLEVEL%
popd
if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%
start "" "%~dp0report.html"
