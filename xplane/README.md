# X-Plane 12 Configuration & Aircraft Modules

This directory contains aircraft-specific integration scripts, response curves, and hardware control profiles for X-Plane 12.

---

## Directory Structure

```
xplane/
├── aircraft/
│   ├── cessna_172_sp/        # Laminar Research C172 SP fixes & magneto drop calibration
│   └── just_flight_c152/     # Just Flight C152 integration & pilot mesh suppression
└── control_profiles/         # X-Plane 12 Joystick & Key profiles (.prf)
    ├── C172 - MOZA AY210 - Joysticks.prf
    ├── C172 - MOZA AY210 - Keys.prf
    ├── C152 - MOZA AY210 - Joysticks.prf
    ├── C152 - MOZA AY210 - Keys.prf
    └── profile_mappings.json # Documentation of Miscellaneous.prf associations
```

---

## Architectural Principles

1. **Non-Destructive Integration:**
   * Files in `control_profiles/` are mapped additively into X-Plane's profile system.
   * `Miscellaneous.prf` maps each aircraft by its internal name (`P acf_profile <AircraftName> <ProfileName>`) so switching aircraft automatically loads the corresponding hardware profile without overwriting default user settings.
2. **Additive Customization:**
   * Each aircraft has its own isolated XLua script directory (`plugins/xlua/scripts/<script_name>/`).
   * Scripts intercept hardware inputs selectively via `wrap_command()` and hook into `before_physics()` only when needed, leaving all other flight dynamics untouched.
3. **Calibrated Response Curves:**
   * **Cessna 172 SP:** Uses Catmull-Rom cubic splines tailored for realistic cable resistance and cruise trim stability.
   * **Cessna 152:** Tuned for the lighter, more agile feel of the shorter-coupled 152 airframe, maintaining full authority at control deflection limits.
