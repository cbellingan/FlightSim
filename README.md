# FlightSim

A unified, modular flight simulation platform combining **X-Plane 12**, **VR headset optimization** (Meta Quest Pro & Quest 3), **Optical Flow Frame Generation** (OFXR-Bridge), **MOZA Force Feedback flight controls** (AY210), and **physically authentic aircraft customizations** (Cessna 172 SP & Just Flight C152).

---

## 🛫 Overview & Key Capabilities

* **VR Razor-Sharp Instrument Clarity:** Dedicated $1.25\times$ SuperSampling, contrast-adaptive sharpening, FOV tangent cropping, and Mini-LED Local Dimming profiles tailored for Meta Quest Pro and Quest 3.
* **OFXR-Bridge Optical Flow 2X Frame Generation:** Silky smooth $72–90\,\text{FPS}$ in VR with low-VRAM optimization for 8GB/12GB/16GB GPUs without fighting Meta ASW.
* **Non-Destructive Additive Architecture:** Profile changes are merged as selective deltas into existing settings without clobbering window bounds, monitor layouts, or custom calibrations.
* **MOZA AY210 Force Feedback Telemetry:** Real-time aerodynamic stiffening ($q = \frac{1}{2}\rho v^2$), propeller propwash elevator lift, ground elevator droop, and harmonic engine rumble tuned specifically to Lycoming IO-360-L2A and O-235-L2C engines.
* **Realistic Aircraft Systems & Magneto Checks:** Fixed X-Plane 12's rotary magneto command locks and calibrated realistic ground run-up magneto drops (~$85\,\text{RPM}$ on C172 at $1800\,\text{RPM}$; ~$75\,\text{RPM}$ on C152 at $1700\,\text{RPM}$).
* **VR Cockpit Cleanliness:** Automated pilot and copilot avatar suppression for the Just Flight C152 so bodies do not clip into the VR headset.

---

## 📁 Repository Structure

```
FlightSim/
├── ARCHITECTURE.md                  # Detailed architectural design & principles
│
├── configurator/                    # VR & Simulation Profile Configurator
│   ├── README.md                    # Configurator user guide & CLI manual
│   ├── ARCHITECTURE.md              # Configurator dimensional compositing architecture
│   ├── configurator.py              # Core Python application & HTTP server
│   ├── ui.html                      # Interactive web dashboard interface
│   ├── profiles/                    # Extensible modular dimension definitions
│   │   ├── vr_headsets/             # Meta Quest Pro, Quest 3, Generic OpenXR
│   │   ├── gpus/                    # RTX 2070 (8GB), 4070 Ti (12GB), 5070 Ti (16GB)
│   │   ├── hardware/                # CPU affinity & flight control bindings
│   │   └── aircraft/                # C172 SP, Just Flight C152
│   ├── launcher.cs                  # Interactive desktop session launcher
│   ├── Launch_XPlane12_VR.bat       # One-click launch batch script
│   └── Open_Configurator.bat        # Web dashboard browser launcher
│
├── xplane/                          # X-Plane 12 Customizations & Aircraft Modules
│   ├── README.md                    # X-Plane integration documentation
│   ├── aircraft/
│   │   ├── cessna_172_sp/           # C172 SP rotary mag wrapping & IO-360-L2A drop
│   │   └── just_flight_c152/        # C152 master ALT/BAT, pitot link & pilot patcher
│   └── control_profiles/            # Joystick response curves & key bindings (.prf)
│       ├── C172 - MOZA AY210 - Joysticks.prf
│       ├── C152 - MOZA AY210 - Joysticks.prf
│       └── profile_mappings.json    # Miscellaneous.prf auto-load table
│
└── moza/                            # MOZA Cockpit & FFB Telemetry
    ├── README.md                    # MOZA setup & tuning manual
    ├── presets/                     # Force Feedback presets (.preset)
    │   ├── {c1720000...}.preset     # C172 SP FFB tuning
    │   └── {c1520000...}.preset     # C152 FFB tuning
    ├── OptimalMatch.vconfig         # Automated aircraft-to-preset matching rules
    └── telemetry_plugin/
        └── win.xpl                  # X-Plane 12 64-bit telemetry bridge plugin
```

---

## ⚡ Quick Start

### 1. Launching the Configurator
Open the interactive web dashboard:
* Run `configurator/Open_Configurator.bat` (or double-click the desktop shortcut).
* Access the UI in any browser at `http://127.0.0.1:8765`.
* Click **🚀 Launch X-Plane 12 VR** to verify the Oculus runtime, arm OFXR-Bridge, apply delta settings, and start X-Plane 12.

### 2. Aircraft Customizations
* **Cessna 172 SP:** Copy scripts from `xplane/aircraft/cessna_172_sp/plugins/xlua/scripts/` to your X-Plane aircraft folder.
* **Just Flight C152:** Copy scripts from `xplane/aircraft/just_flight_c152/plugins/xlua/scripts/` and run `patch_pilots.py` to suppress pilot avatars in VR.

### 3. MOZA AY210 FFB Setup
* Copy presets from `moza/presets/` to `Documents\MOZA Cockpit\PresetLibrary\`.
* Copy `moza/OptimalMatch.vconfig` to `Documents\MOZA Cockpit\PresetLibrary\OptimalMatch.vconfig` for automated profile switching.
* Ensure `moza/telemetry_plugin/win.xpl` is in `C:\X-Plane 12\Resources\plugins\MOZA\64\win.xpl`.

---

## 📖 Detailed Documentation

* For deep architectural insights, see [ARCHITECTURE.md](ARCHITECTURE.md).
* For configurator customization, see [configurator/README.md](configurator/README.md) and [configurator/ARCHITECTURE.md](configurator/ARCHITECTURE.md).
* For aircraft-specific details, see [xplane/README.md](xplane/README.md).
* For force feedback physics details, see [moza/README.md](moza/README.md).
