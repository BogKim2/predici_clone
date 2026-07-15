@echo off
pushd "%~dp0..\.."
python -m test_manuals --pdf "Schuette-Wulkow_Predici-MonteCarlo.pdf" --output "%~dp0"
set EXIT_CODE=%ERRORLEVEL%
popd
if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%
start "" "%~dp0report.html"
