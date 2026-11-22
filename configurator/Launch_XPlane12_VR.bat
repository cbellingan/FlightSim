@echo off
title X-Plane 12 + Meta Quest Pro + OFXR-Bridge + XPME VR Launcher
echo ============================================================================
echo   X-Plane 12 + Meta Quest Pro + OFXR-Bridge + XPME VR Launcher
echo   Hardware Profile: Intel Core i9-9900K ^| RTX 5070 Ti 16GB ^| 64GB RAM
echo ============================================================================
echo.
echo [1/4] Ensuring X-Plane Map Enhancement (XPME) is running...
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
echo [2/4] Applying Meta Quest Pro OpenXR / Link optimizations via OculusDebugToolCLI...
echo       - FOV Tangent Multiplier : 0.80 x 0.74
echo       - Pixel Density Override : 1.30x (SuperSampled Instrument Text)
echo       - Layer Mip-Bias Sharpen : Enabled
echo       - Meta ASW Frame Pacing  : Off
if exist "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe" (
    "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe" -f "C:\Users\cb\.gemini\antigravity\scratch\xplane-quest3-configurator\odt_vr_startup.txt"
) else (
    echo [WARN] OculusDebugToolCLI not found at "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe"
)
echo.
echo [3/4] Ensuring OFXR-Bridge 0.3.1 Optical Flow Tray is armed...
schtasks.exe /Run /TN "OFXRBridgeTrayLaunch" >nul 2>&1
echo.
echo [4/4] Starting X-Plane 12...
schtasks.exe /Run /TN "XPlaneDirectLaunch" >nul 2>&1
if errorlevel 1 (
    cd /d "C:\X-Plane 12"
    explorer.exe "C:\X-Plane 12\X-Plane.exe"
)
echo Done! Put on your Meta Quest Pro headset.
timeout /t 3 >nul
