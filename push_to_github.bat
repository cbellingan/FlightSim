@echo off
cd /d "%~dp0"
echo ========================================================
echo  Pushing FlightSim project to GitHub
echo  Target: https://github.com/cbellingan/FlightSim
echo ========================================================
echo.
git push origin main
if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Successfully pushed all commits to https://github.com/cbellingan/FlightSim!
) else (
    echo.
    echo [NOTE] If a browser login or GitHub prompt appeared, complete sign-in and run this script again.
)
echo.
pause
