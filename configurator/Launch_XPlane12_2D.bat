@echo off
title X-Plane 12 + 2D Ultrawide 5K2K Monitor Launcher
echo ============================================================================
echo   X-Plane 12 + 2D Ultrawide 5K2K Monitor Launcher
echo   Hardware Profile: Intel Core i9-9900K ^| RTX 5070 Ti 16GB ^| 5120x2160
echo ============================================================================
echo.
echo [1/3] Ensuring X-Plane Map Enhancement (XPME) is running...
tasklist /FI "IMAGENAME eq XPlaneMapEnhancement.exe" 2>NUL | find /I /N "XPlaneMapEnhancement.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo       - XPME is already running and streaming scenery from C:\XPME\base.
) else (
    if exist "C:\Program Files\XPlane Map Enhancement\XPlaneMapEnhancement.exe" (
        echo       - Starting XPME from C:\Program Files\XPlane Map Enhancement\XPlaneMapEnhancement.exe...
        start "" "C:\Program Files\XPlane Map Enhancement\XPlaneMapEnhancement.exe"
        timeout /t 3 >nul
    ) else (
        echo       - [NOTE] XPME executable not found at default path.
    )
)
echo.
echo [2/3] Disarming OFXR-Bridge for pure 2D monitor rendering...
taskkill /F /IM OFXRBridgeTray.exe >nul 2>&1
echo.
echo [3/3] Starting X-Plane 12 in Fullscreen 5120x2160...
schtasks.exe /Run /TN "XPlaneDirectLaunch" >nul 2>&1
if errorlevel 1 (
    cd /d "C:\X-Plane 12"
    explorer.exe "C:\X-Plane 12\X-Plane.exe"
)
echo Done! Enjoy flying on your 5K2K ultrawide monitor.
timeout /t 3 >nul
