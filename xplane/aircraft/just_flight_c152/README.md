# Just Flight Cessna 152 Customizations (X-Plane 12)

This directory contains integration modules for the Just Flight / Thranda Cessna 152 (`JF12_C152_v1.0`) optimized for the **MOZA AY210 Force Feedback Yoke** and VR flight.

---

## 1. Modules Included

### `plugins/xlua/scripts/c152_moza/c152_moza.lua`
* **Combined Master ALT/BAT Switch:**
  * Maps the MOZA `BATT` hardware switch to simultaneously toggle **Master Battery** (`sim/cockpit2/electrical/battery_on[0]`) and **Master Alternator** (`sim/cockpit2/electrical/generator_on[0]`).
* **Avionics Switch -> Pitot Heat:**
  * Maps the MOZA Avionics switch (`sim/systems/avionics_on`/`off`) to toggle the C152 Pitot Heat (`sim/cockpit2/ice/ice_pitot_heat_on_pilot`).
* **5-Position Rotary Magnetos:**
  * Direct synchronization across `sim/cockpit2/engine/actuators/ignition_key[0]`, `ignition_on[0]`, and Thranda's 3D key dataref `thranda/starter_key1`.
* **Authentic Lycoming O-235-L2C Magneto Drop:**
  * Real-world POH specification at 1700 RPM runup: **65–85 RPM drop** (max 125 RPM drop).
  * Automatically models the authentic single-magneto drop during ground runup checks.

### `patch_pilots.py` (Pilot Render Suppression)
* Just Flight's C152 renders high-poly pilot and copilot avatars that clip inside the cockpit and headset in VR.
* `patch_pilots.py` cleanly wraps the pilot/copilot geometry blocks in `objects/EXT/Pilots.obj` inside an `ANIM_hide` block, hiding the bodies in both 2D and VR without touching tie-downs, pitot ribbons, or external chocks.
* Usage:
  ```bash
  python patch_pilots.py
  # To restore original mesh:
  python patch_pilots.py --restore
  ```

---

## 2. Installation
1. Install XLua if not already present in the aircraft directory (`plugins/xlua`).
2. Copy `c152_moza.lua` to:
   ```
   C:\X-Plane 12\Aircraft\Just Flight\JF12_C152_v1.0\plugins\xlua\scripts\c152_moza\c152_moza.lua
   ```
3. Run `python patch_pilots.py` to suppress pilot avatars in VR.
