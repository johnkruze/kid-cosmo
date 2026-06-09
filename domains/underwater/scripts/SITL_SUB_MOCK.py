#!/usr/bin/env python3
"""
KID COSMO — SITL SUB Mock v1.0
Simulates a BlueROV2/ArduSub vehicle state for Kid Cosmo integration.
Broadcats MAVLink telemetry for underwater missions.
"""

import time
import socket
import hashlib
import json

def run_mock(target_ip="127.0.0.1", target_port=14550):
    print(f"📡 Starting ArduSub Mock: {target_ip}:{target_port}")
    
    master = mavutil.mavlink_connection(f"udpout:{target_ip}:{target_port}")
    boot_time = time.time()
    step = 0
    cumulative_hash = hashlib.sha256()
    
    while True:
        current_time = time.time() - boot_time
        is_acoustic_loss = current_time > 20 and current_time < 50

        # 1. Heartbeat (ArduSub type) - ONLY SEND IF NOT IN BLACKOUT
        if not is_acoustic_loss:
            master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_SUBMARINE,
                mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED,
                0,
                mavutil.mavlink.MAV_STATE_ACTIVE
            )

        # 2. System Status (Battery)
        master.mav.sys_status_send(
            0, 0, 0, 500, 14800, -1, 92, 0, 0, 0, 0, 0, 0 # 4S Battery
        )

        # 3. Attitude (Underwater currents)
        master.mav.attitude_send(
            int(current_time * 1000),
            0.02 * (step % 5),  # roll
            0.03 * (step % 8),  # pitch
            1.5,                # yaw
            0, 0, 0
        )

        # 4. Pressure/Depth (Simulate deep mission)
        depth = 10.0 + (step * 0.1) # Slowly descending
        pressure = 101325 + (1025 * 9.81 * depth) # Hydrostatic
        
        # EXECUTING GAUSSIAN HASHING: Update cumulative physics fingerprint
        state_bits = {
            "t": round(current_time, 2),
            "depth": round(depth, 2),
            "roll": 0.02 * (step % 5),
            "pitch": 0.03 * (step % 8)
        }
        cumulative_hash.update(json.dumps(state_bits, sort_keys=True).encode())
        current_physics_hash = cumulative_hash.hexdigest()

        # ArduSub uses VFR_HUD.alt for depth (typically negative)
        master.mav.vfr_hud_send(
            0.5,                # airspeed
            0.5,                # groundspeed
            180,                # heading
            50,                 # throttle
            -depth,             # alt (depth as negative altitude)
            -0.1                # climb rate
        )

        # Broadcast Physics Fingerprint via MAVLink STATUSTEXT
        # We prefix with 'HASH:' so the bridge can easily parse it
        master.mav.statustext_send(
            mavutil.mavlink.MAV_SEVERITY_INFO,
            f"HASH:{current_physics_hash}".encode()
        )

        # 5. Acoustic Link Dropout (Simulate loss at T=20)
        is_acoustic_loss = current_time > 20 and current_time < 50
        
        if step % 10 == 0:
            status = "NOMINAL" if not is_acoustic_loss else "⚠️ ACOUSTIC_DROPOUT"
            print(f"🌊 T={current_time:.1f}s | Depth: {depth:.1f}m | Status: {status}")

        # If acoustic loss, we stop sending heartbeats for 3 seconds to trigger blackout
        if not is_acoustic_loss:
            master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_SUBMARINE,
                mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED,
                0,
                mavutil.mavlink.MAV_STATE_ACTIVE
            )

        step += 1
        time.sleep(1.0)

if __name__ == "__main__":
    run_mock()
