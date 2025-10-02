@echo off
REM Script to compact WSL VHDX file
REM Run this script as Administrator

echo Shutting down WSL...
wsl --shutdown
timeout /t 5

echo Compacting VHDX file...
diskpart /s "%~dp0compact_vhdx.txt"

echo VHDX compact completed!
echo.

REM Show file size after compact
powershell -Command "Get-ChildItem 'C:\Users\Dell\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\LocalState\ext4.vhdx' | Select-Object Name, @{Name='Size(GB)';Expression={[Math]::Round($_.Length/1GB,2)}}"

pause