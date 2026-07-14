@echo off
setlocal
set SPHINXBUILD=sphinx-build
set SOURCEDIR=%~dp0
set BUILDDIR=%~dp0_build

if "%1"=="" (
  set BUILDER=html
) else (
  set BUILDER=%1
)

%SPHINXBUILD% -b %BUILDER% "%SOURCEDIR%" "%BUILDDIR%\%BUILDER%"
endlocal
