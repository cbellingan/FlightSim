# MOZA Cockpit & Force Feedback (FFB) Presets

This directory contains Force Feedback presets, automated matching configuration, and the X-Plane 12 telemetry plugin for the **MOZA AY210 Force Feedback Flight Yoke**.

---

## Directory Structure

```
moza/
├── presets/
│   ├── {c1720000-3e98-444a-aaed-a13cd669052f}.preset # AY210 C172 Preset
│   └── {c1520000-3e98-444a-aaed-a13cd669052f}.preset # AY210 C152 Preset
├── OptimalMatch.vconfig                                # Auto-matching configuration
└── telemetry_plugin/
    └── win.xpl                                         # X-Plane 12 64-bit telemetry bridge
```

---

## FFB Aircraft Calibration Comparison

| Parameter | Cessna 172 SP (`{c172...}`) | Cessna 152 (`{c152...}`) | Purpose |
| :--- | :--- | :--- | :--- |
| **Engine Rumble Range** | 450 – 2410 RPM (IO-360) | 600 – 2550 RPM (O-235) | Realistic engine vibration harmonics |
| **Aerodynamic Stiffening Speed** | 44 kt – 148 kt | 38 kt – 111 kt ($V_{NO}$) | Dynamic aerodynamic load build-up |
| **Dynamic Pressure $V_{NE}$** | 163 kt | 149 kt | Max airframe structural limit resistance |
| **Dynamic Pressure Intensity** | 75% | 68% | Reflects lighter C152 control stick force |
| **Elevator Droop Speed** | 35 kt | 30 kt | Yoke droops on ground, rises with propwash |
| **Stall Buffet Onset** | 12° AoA | 11° AoA | Haptic stall warning buffet |
| **Stall Buffet Intensity** | 35% | 32% | Shaker strength at critical AoA |
| **Flap Deployment Buffet** | 20% | 18% | Airflow buffet when deploying flaps |

---

## Installation & Setup

1. **Presets Directory:**
   Copy `.preset` files to:
   ```
   C:\Users\<User>\Documents\MOZA Cockpit\PresetLibrary\
   ```
2. **Automated Matching (`OptimalMatch.vconfig`):**
   Copy `OptimalMatch.vconfig` to `Documents\MOZA Cockpit\PresetLibrary\OptimalMatch.vconfig`. This ensures MOZA Cockpit automatically loads the correct FFB profile the moment an aircraft is loaded in X-Plane 12.
3. **Telemetry Bridge:**
   Ensure `telemetry_plugin/win.xpl` is located in:
   ```
   C:\X-Plane 12\Resources\plugins\MOZA\64\win.xpl
   ```
