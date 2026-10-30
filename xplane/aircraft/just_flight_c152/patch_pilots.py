#!/usr/bin/env python3
"""
Just Flight Cessna 152 - Pilot Render Suppression Patcher
Non-destructively wraps pilot geometry in an ANIM_hide block so pilot/copilot
avatars do not render or clip in VR, while preserving all external elements (pitot cover, etc.).
"""

import argparse
import pathlib
import shutil
import sys

DEFAULT_OBJ = pathlib.Path(r"C:\X-Plane 12\Aircraft\Just Flight\JF12_C152_v1.0\objects\EXT\Pilots.obj")
HIDE_BLOCK_START = "\tANIM_begin\n\tANIM_hide\t0\t1000\tsim/aircraft/electrical/num_batteries\n"
HIDE_BLOCK_END = "\tANIM_end\n"

def patch_pilots_obj(obj_path: pathlib.Path, restore: bool = False):
    if not obj_path.exists():
        print(f"Error: Target file not found at {obj_path}", file=sys.stderr)
        return False

    bak_path = obj_path.with_suffix(".obj.bak")

    if restore:
        if not bak_path.exists():
            print(f"No backup file found at {bak_path}", file=sys.stderr)
            return False
        shutil.copy2(bak_path, obj_path)
        print(f"Restored original {obj_path.name} from backup.")
        return True

    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Check if already patched
    for line in lines[205940:205965]:
        if "sim/aircraft/electrical/num_batteries" in line:
            print("Notice: Pilots.obj is already patched with pilot suppression.")
            return True

    if not bak_path.exists():
        shutil.copy2(obj_path, bak_path)
        print(f"Created safety backup at {bak_path}")

    # Find the pitot cover block end around line 205953
    insert_start = None
    for idx, line in enumerate(lines):
        if idx > 205940 and "thranda/covers/PitotCoverL" in line:
            # find ANIM_end for pitot cover
            for j in range(idx, min(len(lines), idx + 10)):
                if lines[j].strip() == "ANIM_end":
                    insert_start = j + 1
                    break
            break

    if insert_start is None:
        print("Error: Could not locate geometry insertion boundary in Pilots.obj", file=sys.stderr)
        return False

    # Insert end before trailing metadata lines
    insert_end = len(lines) - 2

    new_lines = (
        lines[:insert_start] +
        [HIDE_BLOCK_START] +
        lines[insert_start:insert_end] +
        [HIDE_BLOCK_END] +
        lines[insert_end:]
    )

    with open(obj_path, "w", encoding="utf-8", errors="ignore") as f:
        f.writelines(new_lines)

    print(f"Successfully patched {obj_path.name}. Pilot and copilot avatars are now hidden.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Just Flight C152 Pilot Render Suppression Patcher")
    parser.add_argument("--path", type=pathlib.Path, default=DEFAULT_OBJ, help="Path to Pilots.obj")
    parser.add_argument("--restore", action="store_true", help="Restore original file from backup")
    args = parser.parse_args()

    success = patch_pilots_obj(args.path, restore=args.restore)
    sys.exit(0 if success else 1)
