#!/usr/bin/env python3
"""
KID COSMO — Model Configuration v1.0
Multi-model support for different reasoning profiles.
"""

import os

# Available model profiles for 24GB Apple Silicon
MODEL_PROFILES = {
    # Current fast model - good for high volume mining
    "fast": {
        "name": "Qwen2.5-Coder-7B (Fast)",
        "path": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        "speed": "50-90 t/s",
        "quality": "Good structured JSON, single deliberation",
        "use_case": "High volume manifest mining"
    },

    # DeepSeek for physics-heavy reasoning
    "physics": {
        "name": "DeepSeek-Coder-V2-Lite (Physics)",
        "path": "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx",
        "speed": "30-50 t/s",
        "quality": "Strong math/physics intuition, MoE efficiency",
        "use_case": "Orbital mechanics, thermal dynamics, fuel calculations"
    },

    # Qwen 14B - balanced option
    "balanced": {
        "name": "Qwen2.5-14B-Instruct (Balanced)",
        "path": "mlx-community/Qwen2.5-14B-Instruct-4bit",
        "speed": "25-40 t/s",
        "quality": "Deeper deliberation chains, better edge cases",
        "use_case": "Quality-focused manifest generation"
    }
    # Note: 32B removed - too tight for 24GB Apple Silicon, causes swap pressure
}

def get_model_path(profile: str = None) -> str:
    """Get model path from environment or profile name."""
    # Environment override takes precedence
    env_model = os.environ.get("KIDCOSMO_MODEL")
    if env_model:
        return env_model

    # Check for profile in environment
    env_profile = os.environ.get("KIDCOSMO_PROFILE", "fast")
    profile = profile or env_profile

    if profile in MODEL_PROFILES:
        return MODEL_PROFILES[profile]["path"]

    # Default to fast
    return MODEL_PROFILES["fast"]["path"]

def list_profiles():
    """Print available model profiles."""
    print("\n=== KID COSMO MODEL PROFILES ===\n")
    for key, profile in MODEL_PROFILES.items():
        print(f"[{key}]")
        print(f"  Name: {profile['name']}")
        print(f"  Path: {profile['path']}")
        print(f"  Speed: {profile['speed']}")
        print(f"  Quality: {profile['quality']}")
        print(f"  Use Case: {profile['use_case']}")
        print()

if __name__ == "__main__":
    list_profiles()
    print(f"Current profile: {os.environ.get('KIDCOSMO_PROFILE', 'fast')}")
    print(f"Active model: {get_model_path()}")
