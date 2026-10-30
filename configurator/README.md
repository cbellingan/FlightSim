# X-Plane 12 VR & Flight Configurator

A native, non-destructive configuration orchestrator and launcher designed for **X-Plane 12 in VR**, with deep integration for **Meta Quest Pro / Quest 3**, **OFXR-Bridge Optical Flow Frame Generation**, and **MOZA Force Feedback** hardware.

---

## 1. What It Is & Why It Was Built

Running X-Plane 12 in Virtual Reality—especially on high-resolution headsets like the Meta Quest Pro (QLED Local Dimming) or Quest 3—requires coordinating four independent software layers:
1. **Oculus Link / AirLink Runtime (`OculusDebugToolCLI`):** Pixel density, encode resolution width, bitrate, dynamic FOV tangent multipliers, and ASW mode.
2. **OpenXR API Layer (`OFXR-Bridge`):** Optical Flow Frame Generation, depth reprojection, and Vulkan-to-D3D12 bridge hooks.
3. **X-Plane 12 Preference Files (`X-Plane.prf`, `X-Plane Window Positions.prf`):** VR graphics overrides, RCAS sharpening ratio, anisotropic filtering, texture budgets, and multi-monitor window bounds.
4. **Hardware & Aircraft Telemetry:** MOZA telemetry bridges and aircraft flight dynamics.

Managing these manually requires editing text files, running diagnostic CLI tools, and configuring registry keys before every flight. The **X-Plane 12 VR Configurator** unifies this into a single click with automated state validation, instant rollbacks, and interactive desktop launching.

---

## 2. Key Features

- **Non-Destructive Delta Composition:** Preserves your existing monitor layouts, keybindings, joystick calibrations, and graphics settings. Only target parameters are patched.
- **Dimensional Profile Refactoring:** Profiles are decoupled into four orthogonal dimensions:
  - **VR Headsets** (`quest_pro`, `quest_3`, `generic_openxr`)
  - **GPUs** (`rtx_2070_8gb`, `rtx_4070ti_12gb`, `rtx_5070ti_16gb`)
  - **Hardware & CPU** (`i9_9900k_moza_ay210`, `generic_desktop`)
  - **Aircraft Modules** (`c172_sp`, `jf_c152`)
- **Interactive 1-Click Launch:** Spawns X-Plane 12 directly inside the user's active interactive desktop session (bypassing non-interactive service limitations) and tracks process PID.
- **Automatic Timestamped Backups & 1-Click Restore:** Every apply operation snapshots `X-Plane.prf`, `X-Plane Window Positions.prf`, and Oculus registry keys before writing changes.
- **Embedded Web Dashboard:** Clean, responsive UI with real-time status telemetry, visual profile badges, and diagnostic logs.

---

## 3. How to Use

### Option A: Standalone Executable (Recommended)
Double-click `X-Plane 12 VR Configurator.exe` or click the desktop shortcut.
* Automatically launches the background orchestrator and opens the browser interface at `http://127.0.0.1:8765`.

### Option B: Batch Shortcuts
* **`Open_Configurator.bat`**: Starts the Python backend if not running and opens the Web UI.
* **`Launch_XPlane12_VR.bat`**: Directly applies the default Quest Pro profile and launches X-Plane 12.

### Option C: Python CLI
```bash
# Run web server and open browser
python configurator.py --web

# Apply a specific preset directly via command line
python configurator.py --apply quest_pro_sharp_text

# Check system and runtime status
python configurator.py --status

# List available timestamped backups
python configurator.py --list-backups

# Restore from a backup
python configurator.py --restore 20261025_152807_vr_sweet_spot
```

---

## 4. Web UI Dashboard & Controls

Open `http://127.0.0.1:8765` in any browser:
* **🚀 Launch X-Plane 12 VR:** Verifies Oculus runtime, applies the selected profile, launches OFXR-Bridge tray, and starts X-Plane 12.
* **Apply Profile:** Writes delta configurations immediately to disk.
* **Restore Selected Backup:** 1-click safety rollback to any previous snapshot.
* **Telemetry Diagnostics:** Live status cards for X-Plane preferences, Oculus runtime, and OFXR-Bridge layer.

---

## 5. Directory Structure

```
configurator/
├── README.md               # User & operational documentation (this file)
├── ARCHITECTURE.md         # Detailed architectural documentation
├── configurator.py          # Core Python application & server
├── ui.html                 # Web dashboard interface
├── profiles/               # Modular dimension profiles
│   ├── vr_headsets/        # Headset-specific display & optical parameters
│   ├── gpus/               # VRAM & texture budget presets
│   ├── hardware/           # CPU affinity & flight control bindings
│   └── aircraft/           # Flightmodel & haptic specs
├── launcher.cs             # C# native process launcher
├── Launch_XPlane12_VR.bat  # Quick launch batch script
├── Open_Configurator.bat   # Desktop web UI launch shortcut
└── app.ico                 # App icon
```
