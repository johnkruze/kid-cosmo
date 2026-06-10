#!/usr/bin/env python3
"""
KID COSMO — Zero-Trust Physics C-FFI Bridge
Interfaces Python directly with the high-performance Rust ztp-runtime compiled library.
"""

import os
import sys
import ctypes

# ─── CTYPES STRUCTURES ────────────────────────────────────────────────────────

class C_SoilResult(ctypes.Structure):
    _fields_ = [
        ("max_compaction", ctypes.c_double),
        ("compaction_depth_m", ctypes.c_double),
    ]
    
    def __repr__(self):
        return f"C_SoilResult(max_compaction={self.max_compaction:.4f}, compaction_depth_m={self.compaction_depth_m:.4f})"


class C_SatelliteState(ctypes.Structure):
    _fields_ = [
        ("position", ctypes.c_double * 3),
        ("velocity", ctypes.c_double * 3),
        ("quaternion_attitude", ctypes.c_double * 4),
        ("angular_velocity", ctypes.c_double * 3),
        ("inertia_tensor", ctypes.c_double * 9),
    ]
    
    def __repr__(self):
        pos = list(self.position)
        vel = list(self.velocity)
        quat = list(self.quaternion_attitude)
        w = list(self.angular_velocity)
        return (f"C_SatelliteState(\n"
                f"  pos={pos},\n"
                f"  vel={vel},\n"
                f"  quat={quat},\n"
                f"  ang_vel={w}\n"
                f")")


class C_HandshakeResult(ctypes.Structure):
    _fields_ = [
        ("success", ctypes.c_bool),
        ("resonance", ctypes.c_double),
        ("avg_snr_db", ctypes.c_double),
    ]
    
    def __repr__(self):
        return f"C_HandshakeResult(success={self.success}, resonance={self.resonance:.4f}, avg_snr_db={self.avg_snr_db:.2f}dB)"


class C_MarsState(ctypes.Structure):
    _fields_ = [
        ("position", ctypes.c_double * 3),
        ("velocity", ctypes.c_double * 3),
        ("dry_mass", ctypes.c_double),
        ("drag_area", ctypes.c_double),
        ("cd", ctypes.c_double),
        ("fuel_mass", ctypes.c_double),
        ("specific_impulse", ctypes.c_double),
    ]

    def __repr__(self):
        pos = list(self.position)
        vel = list(self.velocity)
        return (f"C_MarsState(pos={pos}, vel={vel}, fuel={self.fuel_mass:.2f}kg)")


class C_MarsResult(ctypes.Structure):
    _fields_ = [
        ("density", ctypes.c_double),
        ("drag_force", ctypes.c_double * 3),
        ("net_accel", ctypes.c_double * 3),
    ]

    def __repr__(self):
        drag = list(self.drag_force)
        accel = list(self.net_accel)
        return f"C_MarsResult(density={self.density:.6f}, drag={drag}, accel={accel})"


# ─── LIBRARY LOADER ───────────────────────────────────────────────────────────

def load_ztp_library() -> ctypes.CDLL:
    """Find and load the ztp_runtime dynamic library."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Candidate paths relative to this script
    candidates = [
        # Relative to origins/Kid Cosmo/runtime
        os.path.join(script_dir, "../../../../ztp-runtime/target/release/libztp_runtime.dylib"),
        os.path.join(script_dir, "../../ztp-runtime/target/release/libztp_runtime.dylib"),
        # Absolute system paths
        "/Users/aijesusbro/Spectrum/ztp-runtime/target/release/libztp_runtime.dylib",
        # Local relative path
        os.path.join(script_dir, "libztp_runtime.dylib"),
    ]
    
    for path in candidates:
        if os.path.exists(path):
            try:
                lib = ctypes.CDLL(path)
                if os.environ.get("KIDCOSMO_SILENT") != "1":
                    print(f"✅ Loaded ztp_runtime shared library from: {path}")
                return lib
            except Exception as e:
                print(f"⚠️ Failed to load library at {path}: {e}")
                
    # Fallback to standard library search
    try:
        lib = ctypes.CDLL("libztp_runtime.dylib")
        if os.environ.get("KIDCOSMO_SILENT") != "1":
            print("✅ Loaded libztp_runtime.dylib from system library search path.")
        return lib
    except Exception:
        raise FileNotFoundError(
            "CRITICAL: Could not find libztp_runtime.dylib. Please compile ztp-runtime "
            "using `cargo build --release` first."
        )

# Initialize Library & Configure Functions
try:
    _lib = load_ztp_library()
    
    # Configure: ztp_terran_evaluate_contact
    _lib.ztp_terran_evaluate_contact.argtypes = [
        ctypes.c_int32,   # soil_type_code (0: Sand, 1: Loam, 2: Clay, 3: Andisol)
        ctypes.c_double,  # moisture
        ctypes.c_double,  # glomalin_mg_g
        ctypes.c_double,  # compaction
        ctypes.c_uint32,  # depth_layers
        ctypes.c_double,  # mass_kg
        ctypes.c_double,  # footprint_m2
        ctypes.c_int32,   # locomotion_code (0: Wheeled, 1: Tracked, 2: Legged, 3: Drone)
    ]
    _lib.ztp_terran_evaluate_contact.restype = C_SoilResult

    # Configure: ztp_orbital_step_6dof
    _lib.ztp_orbital_step_6dof.argtypes = [
        ctypes.POINTER(C_SatelliteState), # state
        ctypes.c_double,                  # dt
    ]
    _lib.ztp_orbital_step_6dof.restype = None

    # Configure: ztp_orbital_step_attitude
    _lib.ztp_orbital_step_attitude.argtypes = [
        ctypes.POINTER(C_SatelliteState), # state
        ctypes.c_double,                  # ext_torque_x
        ctypes.c_double,                  # ext_torque_y
        ctypes.c_double,                  # ext_torque_z
        ctypes.c_double,                  # dt
    ]
    _lib.ztp_orbital_step_attitude.restype = None

    # Configure: ztp_atheric_handshake
    _lib.ztp_atheric_handshake.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),  # seed_bytes (32 bytes pointer)
        ctypes.c_double,                 # strength
        ctypes.c_double,                 # distance_km
    ]
    _lib.ztp_atheric_handshake.restype = C_HandshakeResult

    # Configure: ztp_mars_step
    _lib.ztp_mars_step.argtypes = [
        ctypes.POINTER(C_MarsState),     # state
        ctypes.c_double,                 # retro_thrust
        ctypes.c_double,                 # dt
    ]
    _lib.ztp_mars_step.restype = C_MarsResult
    
    HAS_ZTP_LIB = True

except Exception as e:
    if os.environ.get("KIDCOSMO_SILENT") != "1":
        print(f"❌ Could not initialize ztp-runtime C bindings: {e}")
    HAS_ZTP_LIB = False


# ─── PYTHON APIS ──────────────────────────────────────────────────────────────

def evaluate_soil(
    soil_type: str,
    moisture: float,
    glomalin: float,
    compaction: float,
    depth_layers: int,
    mass: float,
    footprint: float,
    locomotion: str
) -> C_SoilResult:
    """Wrapper for Terran Soil evaluation."""
    if not HAS_ZTP_LIB:
        raise RuntimeError("ZTP Library not loaded.")
        
    soil_codes = {"sand": 0, "loam": 1, "clay": 2, "andisol": 3}
    loc_codes = {"wheeled": 0, "tracked": 1, "legged": 2, "drone": 3}
    
    soil_code = soil_codes.get(soil_type.lower(), 1)
    loc_code = loc_codes.get(locomotion.lower(), 0)
    
    return _lib.ztp_terran_evaluate_contact(
        soil_code, moisture, glomalin, compaction, depth_layers, mass, footprint, loc_code
    )


def orbital_step_6dof(state: C_SatelliteState, dt: float):
    """Wrapper to run 6DoF orbital step on satellite state."""
    if not HAS_ZTP_LIB:
        raise RuntimeError("ZTP Library not loaded.")
    _lib.ztp_orbital_step_6dof(ctypes.byref(state), dt)


def orbital_step_attitude(state: C_SatelliteState, torques: list, dt: float):
    """Wrapper to run attitude adjustments on satellite state."""
    if not HAS_ZTP_LIB:
        raise RuntimeError("ZTP Library not loaded.")
    _lib.ztp_orbital_step_attitude(
        ctypes.byref(state), torques[0], torques[1], torques[2], dt
    )


def atheric_handshake(seed: bytes, strength: float, distance_km: float) -> C_HandshakeResult:
    """Wrapper for Atheric RF connection checks."""
    if not HAS_ZTP_LIB:
        raise RuntimeError("ZTP Library not loaded.")
        
    if len(seed) < 32:
        seed = seed.ljust(32, b'\x00')
    elif len(seed) > 32:
        seed = seed[:32]
        
    seed_array = (ctypes.c_ubyte * 32)(*seed)
    return _lib.ztp_atheric_handshake(
        ctypes.cast(seed_array, ctypes.POINTER(ctypes.c_ubyte)), strength, distance_km
    )


def mars_step(state: C_MarsState, retro_thrust: float, dt: float) -> C_MarsResult:
    """Wrapper to run Mars EDL step on vehicle state."""
    if not HAS_ZTP_LIB:
        raise RuntimeError("ZTP Library not loaded.")
    return _lib.ztp_mars_step(ctypes.byref(state), retro_thrust, dt)


# ─── QUICK TEST ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if HAS_ZTP_LIB:
        print("\n=== TESTING ZTP C-FFI BRIDGE ===")
        
        # Test 1: Terran Soil
        print("\nTesting Terran contact:")
        res = evaluate_soil("loam", 0.2, 0.5, 0.1, 20, 2000.0, 0.25, "wheeled")
        print(f"  Result: {res}")
        
        # Test 2: Orbital
        print("\nTesting Orbital 6DoF Step:")
        state = C_SatelliteState()
        state.position[0] = 6878.137
        state.velocity[1] = 7.612
        state.quaternion_attitude[0] = 1.0
        state.inertia_tensor[0] = 20.0
        state.inertia_tensor[4] = 20.0
        state.inertia_tensor[8] = 30.0
        
        print(f"  Before: {state}")
        orbital_step_6dof(state, 0.1)
        orbital_step_attitude(state, [0.01, -0.01, 0.005], 0.1)
        print(f"  After: {state}")
        
        # Test 3: Atheric
        print("\nTesting Atheric RF Handshake:")
        test_seed = bytes([i for i in range(32)])
        rf_res = atheric_handshake(test_seed, 10.0, 15.0)
        print(f"  Result: {rf_res}")
        
        # Test 4: Mars EDL
        print("\nTesting Mars EDL Step:")
        m_state = C_MarsState()
        m_state.position[2] = 20000.0  # 20km
        m_state.velocity[2] = -150.0   # descending
        m_state.dry_mass = 1000.0
        m_state.drag_area = 10.0
        m_state.cd = 1.2
        m_state.fuel_mass = 400.0
        m_state.specific_impulse = 290.0
        
        print(f"  Before: {m_state}")
        m_res = mars_step(m_state, 15000.0, 0.1)
        print(f"  After: {m_state}")
        print(f"  FFI Output: {m_res}")

        print("\nAll C-FFI Bridge tests complete.")
    else:
        print("Failed to run tests due to missing library bindings.")
