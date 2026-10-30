# Cessna 172 SP Customizations (X-Plane 12)

This directory contains custom XLua scripts developed for Laminar Research's default Cessna 172 SP to resolve hardware binding limitations and flightmodel inaccuracies when flying with the **MOZA AY210 Force Feedback Yoke**.

---

## 1. Scripts Included

### `plugins/xlua/scripts/c172_starter/c172_starter.lua`
* **Direct Rotary Magneto Command Wrapping:**
  * Intercepts `sim/magnetos/magnetos_off`, `sim/magnetos/magnetos_right_1`, `sim/magnetos/magnetos_left_1`, `sim/magnetos/magnetos_both`, and `sim/starters/engage_starter_1`.
  * Bypasses X-Plane's native rocker-switch toggle logic (`cmp [engine_state], 3`) which locks continuous rotary switches when moving directly between `R` and `L`.
  * Sets both `ignition_key[0]` and `ignition_on[0]` explicitly.
* **Authentic Lycoming IO-360-L2A Magneto Drop:**
  * Real-world POH specification at 1800 RPM runup: **75–125 RPM drop** (max 50 RPM differential).
  * X-Plane's default 5% power drop formula produces an imperceptible ~25–30 RPM drop.
  * Dynamically calculates throttle scaling in `before_physics()` to produce ~**80–85 RPM drop** on `R` and ~**85–95 RPM drop** on `L` at 1800 RPM.
  * Scales down smoothly below 1200 RPM to prevent engine stall during ground taxi checks.

### `plugins/xlua/scripts/c172_electrical/c172_electrical.lua`
* **Combined Master ALT / BAT Switch:**
  * Wraps `sim/electrical/battery_1_on`, `battery_all_on`, `battery_1_off`, `battery_2_off`, and `battery_all_off`.
  * Flipping the single MOZA `BATT` switch snaps both **Master Battery** (`sim/cockpit2/electrical/battery_on[0]`) and **Master Alternator** (`sim/cockpit2/electrical/generator_on[0]`) ON and OFF in lockstep.
  * Uses global command wrapper handles to prevent garbage collection during runtime.

---

## 2. Installation
Copy the scripts to your local X-Plane directory:
```
C:\X-Plane 12\Aircraft\Laminar Research\Cessna 172 SP\plugins\xlua\scripts\
```
A backup of your original script is automatically created with the `.bak` extension.
