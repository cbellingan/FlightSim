@echo off
title X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Launcher
echo ============================================================================
echo   X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Optimizer Launcher
echo   Hardware Profile: Intel Core i9-9900K ^| RTX 2070 8GB ^| 64GB RAM
echo ============================================================================
echo.
echo [1/3] Applying Meta Quest Pro OpenXR / Link optimizations via OculusDebugToolCLI...
echo       - FOV Tangent Multiplier : 0.80 x 0.74
echo       - Pixel Density Override : 1.25x (SuperSampled Instrument Text)
echo       - Layer Mip-Bias Sharpen : Enabled
echo       - Meta ASW Frame Pacing  : Off
if exist "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe" (
    "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe" -f "C:\Users\cb\.gemini\antigravity\scratch\xplane-quest3-configurator\odt_vr_startup.txt"
) else (
    echo [WARN] OculusDebugToolCLI not found at "C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe"
)
echo.
echo [2/3] Ensuring OFXR-Bridge 0.3.1 Optical Flow Tray is armed...
schtasks.exe /Run /TN "OFXRBridgeTrayLaunch" >nul 2>&1
echo.
echo [3/3] Starting X-Plane 12...
schtasks.exe /Run /TN "XPlaneDirectLaunch" >nul 2>&1
if errorlevel 1 (
    cd /d "C:\X-Plane 12"
    explorer.exe "C:\X-Plane 12\X-Plane.exe"
)
echo Done! Put on your Meta Quest Pro headset.
timeout /t 3 >nul
