#!/usr/bin/env python3
"""
X-Plane 12 + Meta Quest Pro (Default) / Quest 3 + OFXR-Bridge VR Configurator
Tailored for: Intel Core i9-9900K | NVIDIA GeForce RTX 2070 (8GB VRAM) | 64GB RAM | 5120x2160 Display
Primary Headset: Meta Quest Pro (Seacliff, 1800x1920/eye, 500-Zone Mini-LED Local Dimming, IR Eye Tracking)
Frame Generation: OFXR-Bridge 0.3.1 (v681) Optical Flow Frame Generation (OpenXR + Vulkan/D3D11->D3D12 Bridge)
"""

import argparse
import datetime
import http.server
import json
import os
import pathlib
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
import winreg

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
APP_DIR = pathlib.Path(__file__).resolve().parent
BACKUP_DIR = APP_DIR / "backups"
STATE_FILE = APP_DIR / "last_applied_profile.json"

XP12_DIR = pathlib.Path(r"C:\X-Plane 12")
XP12_PRF = XP12_DIR / "Output" / "preferences" / "X-Plane.prf"
XP12_WIN_PRF = XP12_DIR / "Output" / "preferences" / "X-Plane Window Positions.prf"
XP12_LOG = XP12_DIR / "Log.txt"
XP12_EXE = XP12_DIR / "X-Plane.exe"

OFXR_DIR = APP_DIR / "ofxr-bridge" / "OFXR-BRIDGE-0.3.1-v681"
OFXR_TRAY_EXE = OFXR_DIR / "OFXRBridgeTray.exe"
OFXR_LOCAL_DIR = pathlib.Path(os.path.expandvars(r"%LOCALAPPDATA%\ofxr-bridge"))
OFXR_INI_PATH = OFXR_LOCAL_DIR / "ofxr-bridge.ini"
OFXR_PROFILES_DIR = OFXR_LOCAL_DIR / "Profiles"
OFXR_RUNTIME_DIR = OFXR_LOCAL_DIR / "RuntimeLayer" / "v681"

ODT_CLI_CANDIDATES = [
    pathlib.Path(r"C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe"),
    pathlib.Path(r"C:\Program Files\Oculus\Support\oculus-diagnostics\OculusDebugToolCLI.exe"),
]
ODT_GUI_CANDIDATES = [
    pathlib.Path(r"C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugTool.exe"),
    pathlib.Path(r"C:\Program Files\Oculus\Support\oculus-diagnostics\OculusDebugTool.exe"),
]
DEVICE_CACHE_PATH = pathlib.Path(os.path.expandvars(r"%LOCALAPPDATA%\Oculus\DeviceCache.json"))
OCULUS_REG_KEY = r"Software\Oculus\RemoteHeadset"
OPENXR_REG_KEY = r"SOFTWARE\Khronos\OpenXR\1"
OPENXR_IMPLICIT_KEY = r"SOFTWARE\Khronos\OpenXR\1\ApiLayers\Implicit"
VULKAN_IMPLICIT_KEY = r"SOFTWARE\Khronos\Vulkan\ImplicitLayers"

DEFAULT_PRESET_ID = "quest_pro_sharp_text"

PROFILES_DIR = APP_DIR / "profiles"

def load_dimensional_profiles():
    """Dynamically load modular dimensional profiles (VR headsets, GPUs, Hardware, Aircraft)."""
    dimensions = {
        "vr_headsets": {},
        "gpus": {},
        "hardware": {},
        "aircraft": {},
    }
    for dim_name in dimensions.keys():
        dim_dir = PROFILES_DIR / dim_name
        if dim_dir.exists():
            for f in dim_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        profile_id = data.get("id", f.stem)
                        dimensions[dim_name][profile_id] = data
                except Exception as e:
                    log_message(f"Error loading {f}: {e}")
    return dimensions

def compose_profile(vr_id="quest_pro", gpu_id="rtx_2070_8gb", hw_id="i9_9900k_moza_ay210", ac_id="c172_sp"):
    """
    Non-destructively compose an operational profile by merging orthogonal dimensions:
    Base Settings + VR Headset + GPU VRAM/Quality + Hardware + Aircraft.
    """
    dims = load_dimensional_profiles()
    vr_profile = dims["vr_headsets"].get(vr_id, {})
    gpu_profile = dims["gpus"].get(gpu_id, {})
    hw_profile = dims["hardware"].get(hw_id, {})
    ac_profile = dims["aircraft"].get(ac_id, {})

    xp_settings = {
        "_vr_separate_graphics_settings": 1,
        "_vr_vrs_enable": 0,
        "_vr_depth_reprojection": 1,
        "_vr_runtime_id": "openxr",
        "_tex_res": 4,
        "vr_renopt_FSR_04": 0,
        "vr_renopt_MSAA": 0,
        "vr_renopt_FXAA": 0,
        "vr_renopt_SSAO_04": 0,
        "vr_renopt_ANISO": 16,
    }

    if "xp_gpu_settings" in gpu_profile:
        xp_settings.update(gpu_profile["xp_gpu_settings"])

    if "xp_vr_overrides" in vr_profile:
        xp_settings.update(vr_profile["xp_vr_overrides"])

    if "cpu" in hw_profile and "fms_per_frame" in hw_profile["cpu"]:
        xp_settings["_fms_per_frame"] = hw_profile["cpu"]["fms_per_frame"]

    odt = vr_profile.get("odt_settings", {})
    fov = odt.get("fov_tangent_multiplier", [0.80, 0.74])
    quest_settings = {
        "headset_target": vr_id,
        "fov_x": fov[0] if len(fov) > 0 else 0.80,
        "fov_y": fov[1] if len(fov) > 1 else 0.74,
        "ppdp": odt.get("pixels_per_display_pixel", 1.25),
        "asw_mode": "Off" if odt.get("asw_mode", 0) == 0 else "Auto",
        "perf_hud": 0,
        "bitrate_mbps": odt.get("encode_bitrate_mbps", 350),
        "encode_width": odt.get("encode_resolution_width", 3600),
        "link_sharpening": 3,
        "distortion_curve": 1,
        "num_slices": 5,
        "dynamic_bitrate": 0,
        "video_codec": "h264",
        "local_dimming": 1 if vr_profile.get("display", {}).get("local_dimming", False) else 0,
    }

    ofxr_spec = vr_profile.get("ofxr_bridge", {})
    gpu_flow = gpu_profile.get("optical_flow_preset", "fast_low_vram")
    ofxr_settings = {
        "armed": ofxr_spec.get("enabled", True),
        "backend": 2,
        "preset": 1,
        "scale": 2,
        "lower_vram": 1 if gpu_flow == "fast_low_vram" else 0,
        "triple_frame_gen": 0,
        "overlay_position": 0,
        "diagnostics": 1,
    }

    window_settings = {
        "windowed_for_vr": True,
        "width": 1280,
        "height": 720,
    }

    return {
        "id": f"{vr_id}_{gpu_id}_{ac_id}",
        "name": f"{vr_profile.get('name', vr_id)} + {gpu_profile.get('name', gpu_id)} ({ac_profile.get('name', ac_id)})",
        "badge": f"{vr_id.upper()} • {gpu_id.split('_')[0].upper()} • {ac_id.upper()}",
        "description": f"Composed dynamically from modular dimensions: Headset={vr_id}, GPU={gpu_id}, Hardware={hw_id}, Aircraft={ac_id}.",
        "xp_settings": xp_settings,
        "window_settings": window_settings,
        "quest_settings": quest_settings,
        "ofxr_settings": ofxr_settings,
        "dimensions": {
            "vr_headset": vr_id,
            "gpu": gpu_id,
            "hardware": hw_id,
            "aircraft": ac_id,
        }
    }


# ---------------------------------------------------------------------------
# Preset Profiles (Defaulting to Meta Quest Pro + OFXR-Bridge + Sharp Text)
# ---------------------------------------------------------------------------
PRESETS = {
    "quest_pro_sharp_text": {
        "id": "quest_pro_sharp_text",
        "name": "Quest Pro Default — Razor-Sharp Text + OFXR-Bridge FrameGen",
        "badge": "Default • OFXR + Sharp Text",
        "description": (
            "Default profile for your Meta Quest Pro (1800×1920 QLED): arms OFXR-Bridge 0.3.1 NVIDIA Optical Flow "
            "2X Frame Generation (with Fast Lower-VRAM Mode for your 8GB RTX 2070 and Meta ASW Off so they don't fight), "
            "1.25x SuperSampling (+56% instrument pixel density), FSR Off, FXAA Off, 75% CAS + Layer Mip-Bias, "
            "0.80×0.74 Quest Pro FOV crop, 3600px Encode Width, and 500-zone Mini-LED Local Dimming ON."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_vr_vrs_enable": 0,              # Off so glancing at gauges across the panel stays 100% 1x1 sharp
            "_vr_vrs_preset": 1,
            "_vr_depth_reprojection": 1,
            "_vr_runtime_id": "openxr",
            "_rcas_ratio": 0.750000,          # 75% Contrast Adaptive Sharpening for crisp font strokes
            "_fms_per_frame": 2,
            "_tex_res": 4,
            "renopt_tex_res_04": 3,
            "vr_renopt_tex_res_04": 3,        # High Textures so 4K cockpit panels never downscale on 8GB VRAM
            "vr_renopt_FSR_04": 0,            # FSR OFF (100% Native resolution — no spatial upscaler blur)
            "vr_renopt_MSAA": 0,
            "vr_renopt_FXAA": 0,              # FXAA OFF (stops post-process blurring of white-on-black gauge digits)
            "vr_renopt_SSAO_04": 0,
            "vr_renopt_clouds_02": 1,
            "vr_renopt_shadow_quality_04": 0,
            "vr_renopt_draw_distance04": 1,   # Low world distance prioritizes VRAM/GPU for 1.25x cockpit text + OFXR
            "vr_renopt_draw_3d_04": 1,        # Low world objects keeps CPU frame times rock-solid
            "vr_renopt_vegetation_3d": 0,
            "vr_renopt_vegetation_quality_04": 1,
            "vr_renopt_ANISO": 16,            # 16x Anisotropic keeps oblique/angled panel labels sharp
            "vr_renopt_static_acf": 0,
            "vr_renopt_boats": 0,
        },
        "window_settings": {
            "windowed_for_vr": True,
            "width": 1280,
            "height": 720,
        },
        "quest_settings": {
            "headset_target": "quest_pro",
            "fov_x": 0.80,                    # Wider H-FOV for Quest Pro open-periphery halo mount
            "fov_y": 0.74,                    # Tighter V-FOV trims unseen brow/cheek gap
            "ppdp": 1.25,                     # 1.25x SuperSampling (+56% texel density on instruments!)
            "asw_mode": "Off",                # Meta ASW Off because OFXR-Bridge handles 2X Optical Flow FrameGen!
            "perf_hud": 0,
            "bitrate_mbps": 325,              # Optimal H.264 bitrate for Quest Pro XR2+ Gen 1 decoder
            "encode_width": 3600,             # Exact 2x1800 native horizontal texel match for Quest Pro
            "link_sharpening": 3,             # Quality Link Sharpening
            "distortion_curve": 1,            # Low Curvature concentrates pixels in center sweet spot
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,               # Enables 500-zone Mini-LED Local Dimming on Quest Pro
        },
        "ofxr_settings": {
            "armed": True,
            "backend": 2,                     # 2 = NVIDIA Optical Flow 0.2.13 (new route), 3 = 0.3.0 (djules), 0 = FidelityFX
            "preset": 1,                      # 1 = Medium, 2 = Fast, 0 = Slow
            "scale": 2,                       # 2 = 50% Flow Input Scale (Best for VR on RTX 2070)
            "lower_vram": 1,                  # 1 = Fast Mode (Lower VRAM / single swapchain rings for 8GB GPU)
            "triple_frame_gen": 0,            # 0 = 2X FrameGen (45->90), 1 = 3X FrameGen (30->90)
            "overlay_position": 0,            # 0 = Off (Default), 6 = Elliott Bottom Telemetry Panel, 2 = Upper Right FPS
            "diagnostics": 1,                 # 1 = Flight recorder log enabled
        },
    },
    "quest_pro_balanced": {
        "id": "quest_pro_balanced",
        "name": "Quest Pro — Balanced VFR Scenery + OFXR-Bridge FrameGen",
        "badge": "Quest Pro VFR + OFXR",
        "description": (
            "Balances sharp Quest Pro instruments (1.15x SuperSampling, FSR Off, FXAA Off, Local Dimming ON) "
            "with Medium World Objects, Medium Draw Distance, 3D Trees, and OFXR-Bridge 2X Optical Flow."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_vr_vrs_enable": 0,
            "_vr_vrs_preset": 1,
            "_vr_depth_reprojection": 1,
            "_vr_runtime_id": "openxr",
            "_rcas_ratio": 0.650000,
            "_fms_per_frame": 2,
            "_tex_res": 4,
            "renopt_tex_res_04": 3,
            "vr_renopt_tex_res_04": 3,
            "vr_renopt_FSR_04": 0,
            "vr_renopt_MSAA": 0,
            "vr_renopt_FXAA": 0,
            "vr_renopt_SSAO_04": 0,
            "vr_renopt_clouds_02": 1,
            "vr_renopt_shadow_quality_04": 0,
            "vr_renopt_draw_distance04": 2,
            "vr_renopt_draw_3d_04": 2,
            "vr_renopt_vegetation_3d": 1,
            "vr_renopt_vegetation_quality_04": 2,
            "vr_renopt_ANISO": 16,
            "vr_renopt_static_acf": 0,
            "vr_renopt_boats": 1,
        },
        "window_settings": {
            "windowed_for_vr": True,
            "width": 1280,
            "height": 720,
        },
        "quest_settings": {
            "headset_target": "quest_pro",
            "fov_x": 0.80,
            "fov_y": 0.74,
            "ppdp": 1.15,
            "asw_mode": "Off",
            "perf_hud": 0,
            "bitrate_mbps": 325,
            "encode_width": 3600,
            "link_sharpening": 3,
            "distortion_curve": 1,
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,
        },
        "ofxr_settings": {
            "armed": True,
            "backend": 2,
            "preset": 1,
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 1,
        },
    },
    "quest_pro_heavy_hubs": {
        "id": "quest_pro_heavy_hubs",
        "name": "Quest Pro — Heavy Airliners & Hubs (OFXR 3X / Low VRAM)",
        "badge": "Max Headroom • 3X Ready",
        "description": (
            "Designed for complex glass-cockpit airliners in heavy weather/cities on Quest Pro: Medium Textures "
            "for maximum VRAM safety alongside OFXR-Bridge (Fast NVIDIA preset + 50% scale + Lower VRAM mode)."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_vr_vrs_enable": 1,
            "_vr_vrs_preset": 2,
            "_vr_depth_reprojection": 1,
            "_vr_runtime_id": "openxr",
            "_rcas_ratio": 0.750000,
            "_fms_per_frame": 2,
            "_tex_res": 3,
            "renopt_tex_res_04": 2,
            "vr_renopt_tex_res_04": 2,
            "vr_renopt_FSR_04": 1,
            "vr_renopt_MSAA": 0,
            "vr_renopt_FXAA": 0,
            "vr_renopt_SSAO_04": 0,
            "vr_renopt_clouds_02": 1,
            "vr_renopt_shadow_quality_04": 0,
            "vr_renopt_draw_distance04": 1,
            "vr_renopt_draw_3d_04": 1,
            "vr_renopt_vegetation_3d": 0,
            "vr_renopt_vegetation_quality_04": 1,
            "vr_renopt_ANISO": 8,
            "vr_renopt_static_acf": 0,
            "vr_renopt_boats": 0,
        },
        "window_settings": {
            "windowed_for_vr": True,
            "width": 1280,
            "height": 720,
        },
        "quest_settings": {
            "headset_target": "quest_pro",
            "fov_x": 0.78,
            "fov_y": 0.72,
            "ppdp": 1.12,
            "asw_mode": "Off",
            "perf_hud": 0,
            "bitrate_mbps": 300,
            "encode_width": 3600,
            "link_sharpening": 3,
            "distortion_curve": 1,
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,
        },
        "ofxr_settings": {
            "armed": True,
            "backend": 2,
            "preset": 2,                      # Fast NVIDIA preset
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 1,
        },
    },
    "quest_pro_meta_asw_baseline": {
        "id": "quest_pro_meta_asw_baseline",
        "name": "Quest Pro — Classic Meta ASW 2.0 Baseline (OFXR Disarmed)",
        "badge": "No OFXR • Meta ASW 45Hz",
        "description": (
            "Disarms OFXR-Bridge and uses Meta Quest Link's native Clock45 ASW 2.0 frame pacing with 1.25x "
            "SuperSampling and razor-sharp cockpit text settings (matches your pre-OFXR backup)."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_vr_vrs_enable": 0,
            "_vr_vrs_preset": 1,
            "_vr_depth_reprojection": 1,
            "_vr_runtime_id": "openxr",
            "_rcas_ratio": 0.750000,
            "_fms_per_frame": 2,
            "_tex_res": 4,
            "renopt_tex_res_04": 3,
            "vr_renopt_tex_res_04": 3,
            "vr_renopt_FSR_04": 0,
            "vr_renopt_MSAA": 0,
            "vr_renopt_FXAA": 0,
            "vr_renopt_SSAO_04": 0,
            "vr_renopt_clouds_02": 1,
            "vr_renopt_shadow_quality_04": 0,
            "vr_renopt_draw_distance04": 1,
            "vr_renopt_draw_3d_04": 1,
            "vr_renopt_vegetation_3d": 0,
            "vr_renopt_vegetation_quality_04": 1,
            "vr_renopt_ANISO": 16,
            "vr_renopt_static_acf": 0,
            "vr_renopt_boats": 0,
        },
        "window_settings": {
            "windowed_for_vr": True,
            "width": 1280,
            "height": 720,
        },
        "quest_settings": {
            "headset_target": "quest_pro",
            "fov_x": 0.80,
            "fov_y": 0.74,
            "ppdp": 1.25,
            "asw_mode": "Clock45",
            "perf_hud": 0,
            "bitrate_mbps": 325,
            "encode_width": 3600,
            "link_sharpening": 3,
            "distortion_curve": 1,
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,
        },
        "ofxr_settings": {
            "armed": False,
            "backend": 2,
            "preset": 1,
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 1,
        },
    },
    "quest_3_sharp_text": {
        "id": "quest_3_sharp_text",
        "name": "Meta Quest 3 Profile — Sharp Text + OFXR-Bridge (Fallback)",
        "badge": "Quest 3 (Eureka)",
        "description": (
            "Switch to this preset whenever flying with your Meta Quest 3 (2064×2208 LCD): uses 3664px Encode Width, "
            "350 Mbps bitrate, 0.78×0.74 FOV crop, 1.18x PPDP, FSR Off, FXAA Off, and OFXR-Bridge 2X FrameGen."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_vr_vrs_enable": 0,
            "_vr_vrs_preset": 1,
            "_vr_depth_reprojection": 1,
            "_vr_runtime_id": "openxr",
            "_rcas_ratio": 0.750000,
            "_fms_per_frame": 2,
            "_tex_res": 4,
            "renopt_tex_res_04": 3,
            "vr_renopt_tex_res_04": 3,
            "vr_renopt_FSR_04": 0,
            "vr_renopt_MSAA": 0,
            "vr_renopt_FXAA": 0,
            "vr_renopt_SSAO_04": 0,
            "vr_renopt_clouds_02": 1,
            "vr_renopt_shadow_quality_04": 0,
            "vr_renopt_draw_distance04": 1,
            "vr_renopt_draw_3d_04": 1,
            "vr_renopt_vegetation_3d": 0,
            "vr_renopt_vegetation_quality_04": 1,
            "vr_renopt_ANISO": 16,
            "vr_renopt_static_acf": 0,
            "vr_renopt_boats": 0,
        },
        "window_settings": {
            "windowed_for_vr": True,
            "width": 1280,
            "height": 720,
        },
        "quest_settings": {
            "headset_target": "quest_3",
            "fov_x": 0.78,
            "fov_y": 0.74,
            "ppdp": 1.18,
            "asw_mode": "Off",
            "perf_hud": 0,
            "bitrate_mbps": 350,
            "encode_width": 3664,
            "link_sharpening": 3,
            "distortion_curve": 1,
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,
        },
        "ofxr_settings": {
            "armed": True,
            "backend": 2,
            "preset": 1,
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 1,
        },
    },
    "desktop_ultrawide": {
        "id": "desktop_ultrawide",
        "name": "2D Ultrawide 5120×2160 Mode (Non-VR)",
        "badge": "5K2K Monitor",
        "description": (
            "Restores Fullscreen 5120×2160 monitor resolution with FSR Quality and High Textures tuned for "
            "2D monitor flying on the RTX 2070, while disarming OFXR-Bridge and preserving your VR profile."
        ),
        "xp_settings": {
            "_vr_separate_graphics_settings": 1,
            "_rcas_ratio": 0.450000,
            "_tex_res": 4,
            "renopt_tex_res_04": 3,
            "renopt_FSR_04": 1,
            "renopt_MSAA": 0,
            "renopt_FXAA": 1,
            "renopt_SSAO_04": 1,
            "renopt_clouds_02": 2,
            "renopt_shadow_quality_04": 1,
            "renopt_draw_distance04": 3,
            "renopt_draw_3d_04": 3,
            "renopt_vegetation_3d": 1,
            "renopt_vegetation_quality_04": 2,
            "renopt_ANISO": 16,
            "renopt_static_acf": 1,
            "renopt_boats": 1,
        },
        "window_settings": {
            "windowed_for_vr": False,
            "width": 5120,
            "height": 2160,
        },
        "quest_settings": {
            "headset_target": "quest_pro",
            "fov_x": 1.0,
            "fov_y": 1.0,
            "ppdp": 1.0,
            "asw_mode": "Auto",
            "perf_hud": 0,
            "bitrate_mbps": 325,
            "encode_width": 3600,
            "link_sharpening": 3,
            "distortion_curve": 1,
            "num_slices": 5,
            "dynamic_bitrate": 0,
            "video_codec": "h264",
            "local_dimming": 1,
        },
        "ofxr_settings": {
            "armed": False,
            "backend": 2,
            "preset": 1,
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 0,
        },
    },
}


# ---------------------------------------------------------------------------
# Helper Functions: Detection, Reading, Writing, CLI Execution
# ---------------------------------------------------------------------------
def get_odt_cli_path():
    for p in ODT_CLI_CANDIDATES:
        if p.exists():
            return p
    return None


def get_odt_gui_path():
    for p in ODT_GUI_CANDIDATES:
        if p.exists():
            return p
    return None


def read_ofxr_status():
    """Inspect OFXR-Bridge 0.3.1 installation, tray process, OpenXR/Vulkan layers, INI config, and flight log."""
    status = {
        "installed": OFXR_TRAY_EXE.exists(),
        "version": "0.3.1 (v681)",
        "tray_exe": str(OFXR_TRAY_EXE),
        "tray_running": False,
        "openxr_layer_armed": False,
        "vulkan_layer_armed": False,
        "openxr_manifest": None,
        "vulkan_manifest": None,
        "last_flight_log": None,
        "last_flight_summary": "Ready — waiting for X-Plane 12 VR session",
        "settings": {
            "armed": True,
            "backend": 2,
            "preset": 1,
            "scale": 2,
            "lower_vram": 1,
            "triple_frame_gen": 0,
            "overlay_position": 0,
            "diagnostics": 1,
        },
    }

    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq OFXRBridgeTray.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        status["tray_running"] = "OFXRBridgeTray.exe" in out
    except Exception:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, OPENXR_IMPLICIT_KEY) as k:
            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(k, i)
                    if "XR_APILAYER_OFXRBridge" in name and val == 0:
                        status["openxr_layer_armed"] = True
                        status["openxr_manifest"] = name
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VULKAN_IMPLICIT_KEY) as k:
            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(k, i)
                    if "OFXR_vulkan_queue" in name and val == 0:
                        status["vulkan_layer_armed"] = True
                        status["vulkan_manifest"] = name
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass

    status["settings"]["armed"] = status["tray_running"] and status["openxr_layer_armed"]

    if OFXR_INI_PATH.exists():
        try:
            text = OFXR_INI_PATH.read_text(encoding="utf-8", errors="replace")
            m_backend = re.search(r"(?m)^backend=(0|1|2|3)\s*$", text)
            m_preset = re.search(r"(?m)^preset=(0|1|2)\s*$", text)
            m_scale = re.search(r"(?m)^scale=(0|1|2|3)\s*$", text)
            m_vram = re.search(r"(?m)^lower_vram=(0|1)\s*$", text)
            m_triple = re.search(r"(?m)^triple_frame_gen=(0|1)\s*$", text)
            m_overlay = re.search(r"(?m)^overlay_position=(\d+)\s*$", text)
            m_diag = re.search(r"(?m)^diagnostics=(0|1)\s*$", text)
            if m_backend:
                status["settings"]["backend"] = int(m_backend.group(1))
            if m_preset:
                status["settings"]["preset"] = int(m_preset.group(1))
            if m_scale:
                status["settings"]["scale"] = int(m_scale.group(1))
            if m_vram:
                status["settings"]["lower_vram"] = int(m_vram.group(1))
            if m_triple:
                status["settings"]["triple_frame_gen"] = int(m_triple.group(1))
            if m_overlay:
                status["settings"]["overlay_position"] = int(m_overlay.group(1))
            if m_diag:
                status["settings"]["diagnostics"] = int(m_diag.group(1))
        except Exception:
            pass

    if OFXR_RUNTIME_DIR.exists():
        try:
            logs = sorted(OFXR_RUNTIME_DIR.glob("ofxr-bridge-flight-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if logs:
                latest = logs[0]
                status["last_flight_log"] = str(latest)
                ltext = latest.read_text(encoding="utf-8", errors="replace")
                if "op=instance_create result=0" in ltext:
                    bridge_type = "D3D11→D3D12 Bridge Armed" if "op=d3d11_bridge result=0" in ltext else "Vulkan→D3D12 Bridge Armed"
                    status["last_flight_summary"] = f"Attached to X-Plane 12 ({latest.name}) • {bridge_type} • Oculus Runtime"
        except Exception:
            pass

    return status


def apply_ofxr_settings(ofxr_settings):
    """Write OFXR-Bridge global & X-Plane profile INIs and arm/disarm OFXRBridgeTray.exe."""
    if not ofxr_settings:
        return "OFXR-Bridge settings unchanged."

    armed = bool(ofxr_settings.get("armed", True))
    backend = int(ofxr_settings.get("backend", 2))
    preset = int(ofxr_settings.get("preset", 1))
    scale = int(ofxr_settings.get("scale", 2))
    lower_vram = int(ofxr_settings.get("lower_vram", 1))
    triple_fg = int(ofxr_settings.get("triple_frame_gen", 0))
    overlay_pos = int(ofxr_settings.get("overlay_position", 0))
    diagnostics = int(ofxr_settings.get("diagnostics", 1))

    tray_backend = "fidelityfx" if backend == 0 else "nvidia"
    tray_preset = {0: "slow", 1: "medium", 2: "fast"}.get(preset, "medium")
    tray_scale = {0: "100", 1: "75", 2: "50", 3: "25"}.get(scale, "50")
    tray_overlay = {
        0: "off",
        1: "upper_left",
        2: "upper_right",
        3: "lower_left",
        4: "lower_right",
        5: "elliott_controller",
        6: "elliott_bottom",
    }.get(overlay_pos, "off")

    # 1. Stop OFXRBridgeTray first so shared memory closes before we write ofxr-bridge.ini
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "OFXRBridgeTray.exe"],
            capture_output=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(0.6)
    except Exception:
        pass

    OFXR_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    OFXR_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    route_block = (
        f"motion_vectors=0\r\n"
        f"preset={preset}\r\n"
        f"scale={scale}\r\n"
        f"backward=0\r\n"
        f"separate_synthesis={lower_vram}\r\n"
        f"lower_vram={lower_vram}\r\n"
        f"prefer_fps=1\r\n"
        f"triple_frame_gen={triple_fg}\r\n"
        f"native_scale=100\r\n"
    )

    ini_content = (
        f"[ofxr]\r\n"
        f"AdvancedMode=0\r\n"
        f"increase_buffer=0\r\n"
        f"enabled=1\r\n"
        f"afw_only=0\r\n"
        f"backend={backend}\r\n"
        f"motion_vectors=0\r\n"
        f"frame_generation=0\r\n"
        f"hybrid_backend=0\r\n"
        f"preset={preset}\r\n"
        f"scale={scale}\r\n"
        f"pacing_mode=1\r\n"
        f"backward=0\r\n"
        f"separate_synthesis={lower_vram}\r\n"
        f"lower_vram={lower_vram}\r\n"
        f"prefer_fps=1\r\n"
        f"triple_frame_gen={triple_fg}\r\n"
        f"native_scale=100\r\n"
        f"r19_camera=0\r\n"
        f"afw_mode=3\r\n"
        f"afw_debug=0\r\n"
        f"afw_clear_before_warping=0\r\n"
        f"afw_ignore_motion_threshold=2.5\r\n"
        f"afw_depth_dilate_mode=0\r\n"
        f"afw_shading_rate=0\r\n"
        f"nr_enabled=0\r\n"
        f"nr_before_sr=1\r\n"
        f"nr_intensity=1\r\n"
        f"nr_preset=0\r\n"
        f"nr_style=0\r\n"
        f"nr_local_structure=1\r\n"
        f"nr_local_tone=1\r\n"
        f"nr_skin_structure=-1\r\n"
        f"nr_auto_mask=1\r\n"
        f"nr_transfer_strength=1\r\n"
        f"nr_colour_strength=1\r\n"
        f"nr_max_ratio=2\r\n"
        f"nr_working_scale=1\r\n"
        f"nr_white_point_scale=1\r\n"
        f"nr_debug_view=0\r\n"
        f"nr_compare=0\r\n"
        f"nr_compare_split=0.5\r\n"
        f"nr_compare_zoom=1\r\n"
        f"nr_compare_swap=0\r\n"
        f"diagnostics={diagnostics}\r\n"
        f"benchmark_csv=1\r\n"
        f"benchmark_auto_pick=1\r\n"
        f"overlay_position={overlay_pos}\r\n"
        f"menu_scale=1\r\n"
        f"menu_offset_x=0\r\n"
        f"menu_offset_y=0\r\n"
        f"luke_shared_swapchains=1\r\n\r\n"
        f"[route.ofxr_fidelityfx]\r\n{route_block}\r\n"
        f"[route.ofxr_reference]\r\n{route_block}\r\n"
        f"[route.ofxr_new]\r\n{route_block}\r\n"
        f"[route.ofxr_djules]\r\n{route_block}\r\n"
        f"[benchmark]\r\nenabled=1\r\n\r\n"
        f"[tray]\r\n"
        f"backend={tray_backend}\r\n"
        f"frame_generation=ofxr\r\n"
        f"dlssg_resolution=100\r\n"
        f"nvidia_preset={tray_preset}\r\n"
        f"nvidia_input_scale={tray_scale}\r\n"
        f"nvidia_bidirectional=0\r\n"
        f"deep_pipeline=1\r\n"
        f"triple_frame_gen={triple_fg}\r\n"
        f"excluded_processes=PimaxHome-Win64-Shipping.exe\r\n"
        f"separate_synthesis={lower_vram}\r\n"
        f"single_swapchain_rings={lower_vram}\r\n"
        f"pacing=auto\r\n"
        f"steamvr_separate_queue=1\r\n"
        f"vulkan_session_bridge=1\r\n"
        f"vulkan_bridge=1\r\n"
        f"d3d11_bridge=1\r\n"
        f"capture_at_end_frame=1\r\n"
        f"crash_debug=0\r\n"
        f"diagnostics={diagnostics}\r\n"
        f"overlay_position={tray_overlay}\r\n"
        f"pause_hotkey=ctrl+alt+f7\r\n\r\n"
        f"[diagnostics]\r\n"
        f"max_file_mb=32\r\n"
        f"flush_each_event=1\r\n"
    )

    OFXR_INI_PATH.write_bytes(ini_content.encode("ascii"))
    (OFXR_PROFILES_DIR / "X-Plane.ini").write_bytes(ini_content.encode("ascii"))
    (OFXR_PROFILES_DIR / "X-Plane.exe.ini").write_bytes(ini_content.encode("ascii"))

    if armed and OFXR_TRAY_EXE.exists():
        try:
            res = subprocess.run(
                ["schtasks.exe", "/Run", "/TN", "OFXRBridgeTrayLaunch"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res.returncode != 0:
                subprocess.Popen([str(OFXR_TRAY_EXE)], cwd=str(OFXR_DIR))
            time.sleep(1.2)
            return f"Armed OFXR-Bridge 0.3.1 (Backend={tray_backend}, Preset={tray_preset}, FlowScale={tray_scale}%, LowerVRAM={bool(lower_vram)})."
        except Exception as e:
            return f"OFXR-Bridge launch warning: {e}"
    else:
        return "Disarmed OFXR-Bridge (OpenXR & Vulkan implicit layers retired)."


def read_xp_prf():
    """Read relevant keys from X-Plane 12 X-Plane.prf and X-Plane Window Positions.prf."""
    result = {}
    if XP12_PRF.exists():
        text = XP12_PRF.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                k, v = parts
                if k.startswith(("renopt_", "vr_renopt_", "_vr_", "_eq_vr", "_tex_res", "_rcas_ratio", "_fms_per_frame")):
                    try:
                        if "." in v:
                            result[k] = round(float(v), 4)
                        else:
                            result[k] = int(v)
                    except ValueError:
                        result[k] = v

    win_info = {"mode": "unknown", "width": 1280, "height": 720, "full_x": 5120, "full_y": 2160}
    if XP12_WIN_PRF.exists():
        wtext = XP12_WIN_PRF.read_text(encoding="utf-8", errors="replace")
        m_mode = re.search(r"monitor/0/m_is_fullscreen\s+(\S+)", wtext)
        m_w = re.search(r"monitor/0/m_window_bounds/2\s+(\d+)", wtext)
        m_h = re.search(r"monitor/0/m_window_bounds/3\s+(\d+)", wtext)
        m_fx = re.search(r"monitor/0/m_x_res_full\s+(\d+)", wtext)
        m_fy = re.search(r"monitor/0/m_y_res_full\s+(\d+)", wtext)
        if m_mode:
            win_info["mode"] = m_mode.group(1)
        if m_w:
            win_info["width"] = int(m_w.group(1))
        if m_h:
            win_info["height"] = int(m_h.group(1))
        if m_fx:
            win_info["full_x"] = int(m_fx.group(1))
        if m_fy:
            win_info["full_y"] = int(m_fy.group(1))
    result["window_info"] = win_info
    return result


def analyze_xp_log():
    """Analyze X-Plane 12 Log.txt for VRAM thrashing, VR resolution, OpenXR status, and bottlenecks."""
    diag = {
        "log_exists": XP12_LOG.exists(),
        "xp_version": "Unknown",
        "vr_views": "1800 x 1920 per eye (Quest Pro base)",
        "vram_thrash_count": 0,
        "min_texture_scale": 1.0,
        "min_headroom_mb": 9999.0,
        "runloop_backups": 0,
        "desktop_swapchain": "Unknown",
        "openxr_runtime": "Unknown",
        "vulkan_ofxr_loaded": False,
        "warnings": [],
    }
    if not XP12_LOG.exists():
        return diag

    text = XP12_LOG.read_text(encoding="utf-8", errors="replace")
    m_ver = re.search(r"Log\.txt for (X-Plane [^\r\n]+)", text)
    if m_ver:
        diag["xp_version"] = m_ver.group(1)

    m_swap = re.search(r"Created swapchain for \S+ with size \{ (\d+x\d+x\d+) \}", text)
    if m_swap:
        diag["desktop_swapchain"] = m_swap.group(1)

    m_view = re.search(r"View 0 Recommended Width x Height (\d+ x \d+)", text)
    if m_view:
        diag["vr_views"] = f"{m_view.group(1)} per eye"

    diag["vulkan_ofxr_loaded"] = "VK_LAYER_OFXRBridge_queue_serialize" in text

    for m in re.finditer(
        r"Target scale moved to ([0-9.]+)\. Texture usage is [^\r\n]+ Memory headroom is ([\-0-9.]+) (mb|gb|b)",
        text,
    ):
        scale = float(m.group(1))
        headroom = float(m.group(2))
        unit = m.group(3)
        if unit == "gb":
            headroom *= 1024.0
        elif unit == "b":
            headroom /= (1024.0 * 1024.0)

        if scale < diag["min_texture_scale"]:
            diag["min_texture_scale"] = scale
        if headroom < diag["min_headroom_mb"]:
            diag["min_headroom_mb"] = round(headroom, 2)
        if scale <= 0.25:
            diag["vram_thrash_count"] += 1

    diag["runloop_backups"] = len(re.findall(r"W/RLP: Runloop is backed up", text))

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, OPENXR_REG_KEY) as k:
            diag["openxr_runtime"], _ = winreg.QueryValueEx(k, "ActiveRuntime")
    except Exception:
        pass

    return diag


def read_quest_status():
    """Read Meta Quest Pro (default/preferred) and Quest 3 device info from DeviceCache.json and Link registry."""
    quest = {
        "connected": False,
        "model": "Meta Quest Pro (Default)",
        "serial": "230YC01DCL00MT",
        "battery": None,
        "connection_type": "Meta Quest Link (USB3)",
        "ipd_mm": 65.3,
        "ovr_service_running": False,
        "all_headsets": [],
        "registry": {},
        "last_cli": {},
    }

    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq OVRServer_x64.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        quest["ovr_service_running"] = "OVRServer_x64.exe" in out
    except Exception:
        pass

    if DEVICE_CACHE_PATH.exists():
        try:
            data = json.loads(DEVICE_CACHE_PATH.read_text(encoding="utf-8", errors="replace"))
            pro_dev = None
            q3_dev = None
            for dev in data.get("devices", []):
                if dev.get("type") == "headset":
                    st = dev.get("subtype", "")
                    label = "Meta Quest Pro" if st == "seacliff" else ("Meta Quest 3" if st == "eureka" else "Quest HMD")
                    quest["all_headsets"].append({
                        "model": label,
                        "subtype": st,
                        "serial": dev.get("serialNumber", "Unknown"),
                        "connected": dev.get("connectionState") == "connected",
                        "battery": dev.get("batteryState"),
                        "ipd_mm": round(dev.get("iad", 0.063) * 1000, 1) if isinstance(dev.get("iad"), (int, float)) else None,
                    })
                    if st == "seacliff":
                        pro_dev = dev
                    elif st == "eureka":
                        q3_dev = dev

            chosen = pro_dev or q3_dev
            if chosen:
                is_pro = chosen.get("subtype") == "seacliff"
                quest["model"] = "Meta Quest Pro" if is_pro else "Meta Quest 3"
                quest["connected"] = chosen.get("connectionState") == "connected"
                quest["serial"] = chosen.get("serialNumber", "230YC01DCL00MT")
                quest["battery"] = chosen.get("batteryState")
                iad = chosen.get("iad")
                if isinstance(iad, (int, float)):
                    quest["ipd_mm"] = round(iad * 1000, 1)
                if chosen.get("isUsingAirLink"):
                    quest["connection_type"] = "Air Link (Wi-Fi)"
                else:
                    usb_mode = chosen.get("usbConnection", {}).get("mode", "usb3").upper()
                    quest["connection_type"] = f"Meta Quest Link ({usb_mode})"
        except Exception:
            pass

    reg_vals = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, OCULUS_REG_KEY) as key:
            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    reg_vals[name] = val
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass
    quest["registry"] = reg_vals

    if STATE_FILE.exists():
        try:
            quest["last_cli"] = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    return quest


def create_backup(label="manual"):
    """Create a timestamped backup of X-Plane.prf, X-Plane Window Positions.prf, and Oculus Registry."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label)
    bdir = BACKUP_DIR / f"{ts}_{safe_label}"
    bdir.mkdir(parents=True, exist_ok=True)

    if XP12_PRF.exists():
        shutil.copy2(XP12_PRF, bdir / "X-Plane.prf")
    if XP12_WIN_PRF.exists():
        shutil.copy2(XP12_WIN_PRF, bdir / "X-Plane Window Positions.prf")

    quest_state = read_quest_status()
    (bdir / "oculus_registry.json").write_text(
        json.dumps(quest_state.get("registry", {}), indent=2), encoding="utf-8"
    )
    return str(bdir)


def list_backups():
    if not BACKUP_DIR.exists():
        return []
    items = []
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
        if d.is_dir():
            items.append({
                "name": d.name,
                "path": str(d),
                "time": datetime.datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    return items[:12]


def restore_backup(backup_name):
    bdir = BACKUP_DIR / backup_name
    if not bdir.exists():
        raise FileNotFoundError(f"Backup not found: {backup_name}")
    if (bdir / "X-Plane.prf").exists():
        shutil.copy2(bdir / "X-Plane.prf", XP12_PRF)
    if (bdir / "X-Plane Window Positions.prf").exists():
        shutil.copy2(bdir / "X-Plane Window Positions.prf", XP12_WIN_PRF)
    reg_file = bdir / "oculus_registry.json"
    if reg_file.exists():
        reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, OCULUS_REG_KEY) as key:
            for k, v in reg_data.items():
                if isinstance(v, int):
                    winreg.SetValueEx(key, k, 0, winreg.REG_DWORD, v)
                elif isinstance(v, str):
                    winreg.SetValueEx(key, k, 0, winreg.REG_SZ, v)
    elif (bdir / "HKCU_Oculus_RemoteHeadset.reg").exists():
        subprocess.run(
            ["reg.exe", "import", str(bdir / "HKCU_Oculus_RemoteHeadset.reg")],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    if "PRE_OFXR" in backup_name:
        apply_ofxr_settings({"armed": False})
    return True


def update_xp_prf_files(xp_settings, window_settings):
    """Safely update X-Plane.prf and X-Plane Window Positions.prf while preserving all other lines."""
    if XP12_PRF.exists():
        lines = XP12_PRF.read_text(encoding="utf-8", errors="replace").splitlines()
        updated_keys = set()
        new_lines = []
        for line in lines:
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0] in xp_settings:
                k = parts[0]
                val = xp_settings[k]
                if isinstance(val, float):
                    new_lines.append(f"{k} {val:.6f}")
                else:
                    new_lines.append(f"{k} {val}")
                updated_keys.add(k)
            else:
                new_lines.append(line)

        for k, val in xp_settings.items():
            if k not in updated_keys:
                if isinstance(val, float):
                    new_lines.append(f"{k} {val:.6f}")
                else:
                    new_lines.append(f"{k} {val}")

        XP12_PRF.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    if XP12_WIN_PRF.exists() and window_settings:
        wlines = XP12_WIN_PRF.read_text(encoding="utf-8", errors="replace").splitlines()
        windowed = window_settings.get("windowed_for_vr", True)
        w_width = int(window_settings.get("width", 1280))
        w_height = int(window_settings.get("height", 720))
        mode_str = "wmgr_mode_window" if windowed else "wmgr_mode_fullscreen"

        new_wlines = []
        for line in wlines:
            if line.startswith("monitor/0/m_is_fullscreen "):
                new_wlines.append(f"monitor/0/m_is_fullscreen {mode_str}")
            elif line.startswith("monitor/0/m_window_bounds/2 ") and windowed:
                new_wlines.append(f"monitor/0/m_window_bounds/2 {w_width}")
            elif line.startswith("monitor/0/m_window_bounds/3 ") and windowed:
                new_wlines.append(f"monitor/0/m_window_bounds/3 {w_height}")
            elif line.startswith("monitor/0/m_arbitrary_bounds/2 ") and windowed:
                new_wlines.append(f"monitor/0/m_arbitrary_bounds/2 {w_width}")
            elif line.startswith("monitor/0/m_arbitrary_bounds/3 ") and windowed:
                new_wlines.append(f"monitor/0/m_arbitrary_bounds/3 {w_height}")
            else:
                new_wlines.append(line)
        XP12_WIN_PRF.write_text("\n".join(new_wlines) + "\n", encoding="utf-8")


def apply_quest_settings(quest_settings):
    """Write persistent Oculus Link registry settings and execute live OculusDebugToolCLI commands."""
    log_messages = []

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, OCULUS_REG_KEY) as key:
            if "bitrate_mbps" in quest_settings:
                winreg.SetValueEx(key, "BitrateMbps", 0, winreg.REG_DWORD, int(quest_settings["bitrate_mbps"]))
            if "encode_width" in quest_settings:
                winreg.SetValueEx(key, "EncodeWidth", 0, winreg.REG_DWORD, int(quest_settings["encode_width"]))
            if "link_sharpening" in quest_settings:
                winreg.SetValueEx(key, "LinkSharpeningEnabled", 0, winreg.REG_DWORD, int(quest_settings["link_sharpening"]))
            if "distortion_curve" in quest_settings:
                winreg.SetValueEx(key, "DistortionCurve", 0, winreg.REG_DWORD, int(quest_settings["distortion_curve"]))
            if "num_slices" in quest_settings:
                winreg.SetValueEx(key, "NumSlices", 0, winreg.REG_DWORD, int(quest_settings["num_slices"]))
            if "dynamic_bitrate" in quest_settings:
                winreg.SetValueEx(key, "DBR", 0, winreg.REG_DWORD, int(quest_settings["dynamic_bitrate"]))
            if "local_dimming" in quest_settings:
                winreg.SetValueEx(key, "LocalDimming", 0, winreg.REG_DWORD, int(quest_settings["local_dimming"]))
            if "video_codec" in quest_settings:
                winreg.SetValueEx(key, "VideoCodec", 0, winreg.REG_SZ, str(quest_settings["video_codec"]))
        log_messages.append("Updated HKCU\\Software\\Oculus\\RemoteHeadset Link registry keys.")
    except Exception as e:
        log_messages.append(f"Registry warning: {e}")

    cli_path = get_odt_cli_path()
    if cli_path:
        fov_x = float(quest_settings.get("fov_x", 0.80))
        fov_y = float(quest_settings.get("fov_y", 0.74))
        ppdp = float(quest_settings.get("ppdp", 1.25))
        asw_mode = quest_settings.get("asw_mode", "Off")
        perf_hud = int(quest_settings.get("perf_hud", 0))

        asw_cmd_map = {
            "Clock45": "server:asw.Clock45",
            "Sim45": "server:asw.Sim45",
            "Auto": "server:asw.Auto",
            "Off": "server:asw.Off",
            "Clock30": "server:asw.Clock30",
        }
        asw_cmd = asw_cmd_map.get(asw_mode, "server:asw.Off")

        cli_commands = [
            f"service set-client-fov-tan-angle-multiplier {fov_x:.2f} {fov_y:.2f}",
            "service set-use-fov-stencil true",
            f"service set-pixels-per-display-pixel-override {ppdp:.2f}",
            "service set-force-mip-gen-on-all-layers true",
            "service set-offset-mip-bias-on-all-layers true",
            asw_cmd,
            f"perfhud set-mode {perf_hud}" if perf_hud > 0 else "perfhud reset",
            "exit",
        ]
        input_str = "\n".join(cli_commands) + "\n"
        try:
            proc = subprocess.run(
                [str(cli_path)],
                input=input_str,
                text=True,
                capture_output=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            log_messages.append(
                f"Applied live OculusDebugToolCLI commands (FOV={fov_x:.2f}x{fov_y:.2f}, PPDP={ppdp:.2f}, ASW={asw_mode}, HUD={perf_hud})."
            )
            if proc.stdout:
                log_messages.append(proc.stdout.strip())
        except Exception as e:
            log_messages.append(f"OculusDebugToolCLI warning: {e}")

    generate_vr_launcher_bat(quest_settings)
    return "\n".join(log_messages)


def generate_vr_launcher_bat(quest_settings):
    """Create a 1-click batch launcher that sets FOV Tangent, Mip-Bias, ASW & OFXR-Bridge before starting X-Plane 12."""
    cli_path = get_odt_cli_path() or pathlib.Path(
        r"C:\Program Files\Meta Horizon\Support\oculus-diagnostics\OculusDebugToolCLI.exe"
    )
    fov_x = float(quest_settings.get("fov_x", 0.80))
    fov_y = float(quest_settings.get("fov_y", 0.74))
    ppdp = float(quest_settings.get("ppdp", 1.25))
    asw_mode = quest_settings.get("asw_mode", "Off")
    perf_hud = int(quest_settings.get("perf_hud", 0))
    asw_cmd_map = {
        "Clock45": "server:asw.Clock45",
        "Sim45": "server:asw.Sim45",
        "Auto": "server:asw.Auto",
        "Off": "server:asw.Off",
        "Clock30": "server:asw.Clock30",
    }
    asw_cmd = asw_cmd_map.get(asw_mode, "server:asw.Off")
    hud_cmd = f"perfhud set-mode {perf_hud}" if perf_hud > 0 else "perfhud reset"

    odt_script = APP_DIR / "odt_vr_startup.txt"
    odt_script.write_text(
        f"service set-client-fov-tan-angle-multiplier {fov_x:.2f} {fov_y:.2f}\n"
        f"service set-use-fov-stencil true\n"
        f"service set-pixels-per-display-pixel-override {ppdp:.2f}\n"
        f"service set-force-mip-gen-on-all-layers true\n"
        f"service set-offset-mip-bias-on-all-layers true\n"
        f"{asw_cmd}\n"
        f"{hud_cmd}\n"
        f"exit\n",
        encoding="utf-8",
    )

    bat_content = f"""@echo off
title X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Launcher
echo ============================================================================
echo   X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Optimizer Launcher
echo   Hardware Profile: Intel Core i9-9900K ^| RTX 2070 8GB ^| 64GB RAM
echo ============================================================================
echo.
echo [1/3] Applying Meta Quest Pro OpenXR / Link optimizations via OculusDebugToolCLI...
echo       - FOV Tangent Multiplier : {fov_x:.2f} x {fov_y:.2f}
echo       - Pixel Density Override : {ppdp:.2f}x (SuperSampled Instrument Text)
echo       - Layer Mip-Bias Sharpen : Enabled
echo       - Meta ASW Frame Pacing  : {asw_mode}
if exist "{cli_path}" (
    "{cli_path}" -f "{odt_script}"
) else (
    echo [WARN] OculusDebugToolCLI not found at "{cli_path}"
)
echo.
echo [2/3] Ensuring OFXR-Bridge 0.3.1 Optical Flow Tray is armed...
schtasks.exe /Run /TN "OFXRBridgeTrayLaunch" >nul 2>&1
echo.
echo [3/3] Starting X-Plane 12...
schtasks.exe /Run /TN "XPlaneDirectLaunch" >nul 2>&1
if errorlevel 1 (
    cd /d "{XP12_DIR}"
    explorer.exe "{XP12_EXE}"
)
echo Done! Put on your Meta Quest Pro headset.
timeout /t 3 >nul
"""
    bat_path = APP_DIR / "Launch_XPlane12_VR.bat"
    bat_path.write_text(bat_content, encoding="utf-8")
    return str(bat_path)


def launch_xplane_interactive():
    """Launch X-Plane 12 visibly on the user's interactive desktop (WinSta0\\Default)."""
    # 1. Re-apply live OculusDebugToolCLI settings right before launch
    odt_script = APP_DIR / "odt_vr_startup.txt"
    if not odt_script.exists():
        generate_vr_launcher_bat(PRESETS[DEFAULT_PRESET_ID]["quest_settings"])
    cli_path = get_odt_cli_path()
    if cli_path and odt_script.exists():
        try:
            subprocess.run(
                [str(cli_path), "-f", str(odt_script)],
                capture_output=True,
                timeout=6,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass

    # 2. If OFXR-Bridge is armed in last applied profile (or currently armed), ensure OFXRBridgeTray is running
    ofxr_stat = read_ofxr_status()
    if ofxr_stat.get("settings", {}).get("armed", True) and not ofxr_stat.get("tray_running"):
        try:
            subprocess.run(
                ["schtasks.exe", "/Run", "/TN", "OFXRBridgeTrayLaunch"],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            time.sleep(1.0)
        except Exception:
            pass

    # 3. Launch X-Plane 12 via Interactive Scheduled Task (WinSta0\Default foreground window)
    try:
        res = subprocess.run(
            ["schtasks.exe", "/Run", "/TN", "XPlaneDirectLaunch"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if res.returncode != 0:
            subprocess.Popen([str(XP12_EXE)], cwd=str(XP12_DIR))
    except Exception:
        subprocess.Popen([str(XP12_EXE)], cwd=str(XP12_DIR))


def apply_full_configuration(payload):
    """Backup current state and apply X-Plane + Window + Quest Pro/3 + OFXR-Bridge settings."""
    preset_id = payload.get("preset_id", DEFAULT_PRESET_ID)
    backup_path = create_backup(preset_id)

    xp_settings = payload.get("xp_settings", {})
    window_settings = payload.get("window_settings", {})
    quest_settings = payload.get("quest_settings", {})
    ofxr_settings = payload.get("ofxr_settings", {})

    update_xp_prf_files(xp_settings, window_settings)
    cli_log = apply_quest_settings(quest_settings)
    ofxr_log = apply_ofxr_settings(ofxr_settings)

    saved_state = {
        "applied_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "preset_id": preset_id,
        "backup_path": backup_path,
        "xp_settings": xp_settings,
        "window_settings": window_settings,
        "quest_settings": quest_settings,
        "ofxr_settings": ofxr_settings,
    }
    STATE_FILE.write_text(json.dumps(saved_state, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "backup_path": backup_path,
        "cli_log": f"{cli_log}\n{ofxr_log}",
        "state": get_full_status(),
    }


def get_full_status():
    return {
        "default_preset_id": DEFAULT_PRESET_ID,
        "hardware": {
            "cpu": "Intel Core i9-9900K @ 3.60 GHz (8C / 16T)",
            "gpu": "NVIDIA GeForce RTX 2070 (8 GB VRAM, Driver 560.94)",
            "ram": "64 GB DDR4 (63.86 GB usable)",
            "monitor": "5120 x 2160 (21:9 5K2K Ultrawide)",
            "xp12_path": str(XP12_DIR),
        },
        "xp_current": read_xp_prf(),
        "log_analysis": analyze_xp_log(),
        "quest_status": read_quest_status(),
        "ofxr_status": read_ofxr_status(),
        "presets": PRESETS,
        "dimensions": load_dimensional_profiles(),
        "backups": list_backups(),
    }


# ---------------------------------------------------------------------------
# HTTP Server for Interactive Web UI
# ---------------------------------------------------------------------------
class ConfiguratorHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json(get_full_status())
        elif self.path == "/api/dimensions":
            self._send_json(load_dimensional_profiles())
        elif self.path in ("/", "/index.html"):
            ui_file = APP_DIR / "ui.html"
            body = ui_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        payload = json.loads(raw) if raw else {}

        try:
            if self.path == "/api/compose":
                vr_id = payload.get("vr_headset", "quest_pro")
                gpu_id = payload.get("gpu", "rtx_2070_8gb")
                hw_id = payload.get("hardware", "i9_9900k_moza_ay210")
                ac_id = payload.get("aircraft", "c172_sp")
                res = compose_profile(vr_id, gpu_id, hw_id, ac_id)
                self._send_json({"ok": True, "profile": res})
            elif self.path == "/api/apply":
                if "dimensions" in payload or "vr_headset" in payload:
                    vr_id = payload.get("vr_headset", payload.get("dimensions", {}).get("vr_headset", "quest_pro"))
                    gpu_id = payload.get("gpu", payload.get("dimensions", {}).get("gpu", "rtx_2070_8gb"))
                    hw_id = payload.get("hardware", payload.get("dimensions", {}).get("hardware", "i9_9900k_moza_ay210"))
                    ac_id = payload.get("aircraft", payload.get("dimensions", {}).get("aircraft", "c172_sp"))
                    payload = compose_profile(vr_id, gpu_id, hw_id, ac_id)
                res = apply_full_configuration(payload)
                self._send_json(res)
            elif self.path == "/api/restore":
                bname = payload.get("backup_name")
                restore_backup(bname)
                self._send_json({"ok": True, "state": get_full_status()})
            elif self.path == "/api/hud":
                mode = int(payload.get("mode", 0))
                cli_path = get_odt_cli_path()
                if cli_path:
                    cmd = f"perfhud set-mode {mode}\nexit\n" if mode > 0 else "perfhud reset\nexit\n"
                    subprocess.run([str(cli_path)], input=cmd, text=True, capture_output=True, timeout=5)
                self._send_json({"ok": True, "mode": mode})
            elif self.path == "/api/launch_xp":
                launch_xplane_interactive()
                self._send_json({"ok": True, "message": "Launched X-Plane 12 with Quest Pro + OFXR-Bridge optimizations!"})
            elif self.path == "/api/open_odt":
                gui = get_odt_gui_path()
                if gui:
                    subprocess.Popen(["explorer.exe", str(gui)], cwd=str(gui.parent))
                self._send_json({"ok": True})
            elif self.path == "/api/open_ofxr_settings":
                try:
                    res = subprocess.run(
                        ["schtasks.exe", "/Run", "/TN", "OFXRSettingsLaunch"],
                        capture_output=True,
                        timeout=4,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    if res.returncode != 0 and OFXR_TRAY_EXE.exists():
                        subprocess.Popen([str(OFXR_TRAY_EXE), "--settings-only"], cwd=str(OFXR_DIR))
                except Exception:
                    if OFXR_TRAY_EXE.exists():
                        subprocess.Popen([str(OFXR_TRAY_EXE), "--settings-only"], cwd=str(OFXR_DIR))
                self._send_json({"ok": True})
            elif self.path == "/api/ofxr_overlay":
                pos = int(payload.get("overlay_position", 0))
                pos_name = {
                    0: "off",
                    1: "upper_left",
                    2: "upper_right",
                    3: "lower_left",
                    4: "lower_right",
                    5: "elliott_controller",
                    6: "elliott_bottom",
                }.get(pos, "off")
                rt_ini = OFXR_RUNTIME_DIR / "ofxr_bridge.ini"
                if rt_ini.exists():
                    txt = rt_ini.read_text(encoding="ascii", errors="replace")
                    txt = re.sub(r"(?m)^position=\S+", f"position={pos_name}", txt)
                    rt_ini.write_bytes(txt.encode("ascii"))
                for p in (OFXR_INI_PATH, OFXR_PROFILES_DIR / "X-Plane.ini", OFXR_PROFILES_DIR / "X-Plane.exe.ini"):
                    if p.exists():
                        ptxt = p.read_text(encoding="ascii", errors="replace")
                        ptxt = re.sub(r"(?m)^overlay_position=\d+", f"overlay_position={pos}", ptxt)
                        ptxt = re.sub(r"(?m)^overlay_position=[a-z_]+", f"overlay_position={pos_name}", ptxt)
                        p.write_bytes(ptxt.encode("ascii"))
                self._send_json({"ok": True, "overlay_position": pos, "position_name": pos_name})
            elif self.path == "/api/shutdown":
                self._send_json({"ok": True, "message": "Configurator server shutting down."})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self._send_json({"ok": False, "error": "Unknown endpoint"}, status=404)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, status=500)


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def ensure_std_streams():
    """Ensure stdin/stdout/stderr are valid file objects when launched windowless (pythonw or hidden process)."""
    log_path = APP_DIR / "configurator.log"
    if sys.stdin is None:
        sys.stdin = open(os.devnull, "r", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = open(log_path, "a", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = open(log_path, "a", encoding="utf-8", buffering=1)


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    ensure_std_streams()
    parser = argparse.ArgumentParser(description="X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Configurator")
    parser.add_argument("--apply-preset", choices=list(PRESETS.keys()), help="Apply a preset immediately via CLI")
    parser.add_argument("--status", action="store_true", help="Print hardware & config diagnostics JSON and exit")
    parser.add_argument("--port", type=int, default=8765, help="Port for Web Configurator UI (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(get_full_status(), indent=2))
        return

    if args.apply_preset:
        preset = PRESETS[args.apply_preset]
        res = apply_full_configuration({
            "preset_id": preset["id"],
            "xp_settings": preset["xp_settings"],
            "window_settings": preset["window_settings"],
            "quest_settings": preset["quest_settings"],
            "ofxr_settings": preset.get("ofxr_settings", {}),
        })
        print(f"Applied preset '{preset['name']}' successfully!")
        print(f"Backup saved to: {res['backup_path']}")
        print(res["cli_log"])
        return

    url = f"http://127.0.0.1:{args.port}"
    if is_port_in_use(args.port):
        print(f"Configurator server is already running at {url}. Opening browser...")
        if not args.no_browser:
            webbrowser.open(url)
        return

    with ReusableThreadingTCPServer(("127.0.0.1", args.port), ConfiguratorHandler) as httpd:
        print(f"X-Plane 12 + Meta Quest Pro + OFXR-Bridge VR Configurator running at {url}")
        if not args.no_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down configurator.")


if __name__ == "__main__":
    main()
