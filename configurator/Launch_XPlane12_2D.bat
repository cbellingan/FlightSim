@echo off
title X-Plane 12 + 2D Ultrawide 5K2K Monitor Launcher
echo ============================================================================
echo   X-Plane 12 + 2D Ultrawide 5K2K Monitor Launcher
echo   Hardware Profile: Intel Core i9-9900K ^| RTX 5070 Ti 16GB ^| 5120x2160
echo ============================================================================
echo.
echo [1/4] Applying 2D Ultrawide 5K2K profile (_eq_vr 0, Fullscreen 5120x2160)...
python "C:\Users\cb\.gemini\antigravity\scratch\xplane-quest3-configurator\configurator.py" --apply-preset desktop_ultrawide
echo.
echo [2/4] Ensuring X-Plane Map Enhancement (XPME) is running...
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
echo [3/4] Disarming OFXR-Bridge for pure 2D monitor rendering...
taskkill /F /IM OFXRBridgeTray.exe >nul 2>&1
echo.
echo [4/4] Starting X-Plane 12 in Fullscreen 5120x2160...
schtasks.exe /Run /TN "XPlaneDirectLaunch" >nul 2>&1
if errorlevel 1 (
    cd /d "C:\X-Plane 12"
    explorer.exe "C:\X-Plane 12\X-Plane.exe"
)
echo Done! Enjoy flying on your 5K2K ultrawide monitor.
timeout /t 3 >nul
