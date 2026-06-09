#!/usr/bin/env python3
"""
KID COSMO — MAVLink Bridge v1.0
Transmutes raw ArduPilot telemetry into Kid Cosmo Decision Context.
"""

import time
import json
import socket
from pymavlink import mavutil
from typing import Dict, Any

class MAVLinkBridge:
    def __init__(self, connection_str: str = "udpin:localhost:14550"):
        print(f"📡 Initializing Kid Cosmo Bridge: {connection_str}")
        self.master = mavutil.mavlink_connection(connection_str)
        self.last_heartbeat = 0
        self.telemetry = {
            "mode": "UNKNOWN",
            "gps_fix": 0,
            "sat_count": 0,
            "battery_v": 0,
            "battery_pct": 0,
            "pitch": 0.0,
            "roll": 0.0,
            "yaw": 0.0,
            "alt": 0.0
        }
        self.is_blackout = False
        self.current_physics_hash = "0x0000"

    def wait_for_heartbeat(self):
        print("⌛ Waiting for ArduPilot heartbeat...")
        self.master.wait_heartbeat()
        self.last_heartbeat = time.time()
        print("✅ Heartbeat received!")

    def update(self):
        # Heartbeat timeout check
        if time.time() - self.last_heartbeat > 3.0:
            if not self.is_blackout:
                print("🌑 EXCLUSION ZONE DETECTED: Ground Control Link Severed.")
                self.is_blackout = True

        msg = self.master.recv_match(blocking=False)
        if not msg:
            return

        msg_type = msg.get_type()
        
        if msg_type == "HEARTBEAT":
            self.last_heartbeat = time.time()
            self.is_blackout = False
            self.telemetry["mode"] = mavutil.mode_mapping_acm.get(msg.custom_mode, "UNKNOWN")
            
        elif msg_type == "SYS_STATUS":
            self.telemetry["battery_v"] = msg.voltage_battery / 1000.0
            self.telemetry["battery_pct"] = msg.battery_remaining
            
        elif msg_type == "GPS_RAW_INT":
            self.telemetry["gps_fix"] = msg.fix_type
            self.telemetry["sat_count"] = msg.satellites_visible
            
        elif msg_type == "ATTITUDE":
            self.telemetry["pitch"] = msg.pitch
            self.telemetry["roll"] = msg.roll
            self.telemetry["yaw"] = msg.yaw
            
        elif msg_type == "VFR_HUD":
            self.telemetry["alt"] = msg.alt
            
        elif msg_type == "STATUSTEXT":
            text = msg.text
            if text.startswith("HASH:"):
                self.current_physics_hash = text.split("HASH:")[1]

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns a Kid Cosmo compatible telemetry snapshot."""
        return {
            "t": round(time.time(), 3),
            "status": {
                "mode": self.telemetry["mode"],
                "battery": self.telemetry["battery_pct"],
                "voltage": self.telemetry["battery_v"]
            },
            "perception": {
                "gps_fix": self.telemetry["gps_fix"],
                "sats": self.telemetry["sat_count"],
                "attitude": {
                    "p": round(self.telemetry["pitch"], 3),
                    "r": round(self.telemetry["roll"], 3),
                    "y": round(self.telemetry["yaw"], 3)
                },
                "alt": round(self.telemetry["alt"], 2)
            },
            "is_blackout": self.is_blackout,
            "parent_trajectory_hash": self.current_physics_hash
        }

    def set_mode(self, mode_name: str):
        """Changes the ArduPilot flight mode."""
        if mode_name not in self.master.mode_mapping():
            print(f"❌ Unknown mode: {mode_name}")
            return
        mode_id = self.master.mode_mapping()[mode_name]
        self.master.mav.set_mode_send(
            self.master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
        print(f"🕹️ MAVLink: Mode set to {mode_name}")

    def send_rc_override(self, pitch=1500, roll=1500, throttle=1500, yaw=1500):
        """Sends RC channel overrides (emergency somatic control)."""
        # channels 1-4: roll, pitch, throttle, yaw
        channels = [roll, pitch, throttle, yaw, 0, 0, 0, 0]
        self.master.mav.rc_channels_override_send(
            self.master.target_system,
            self.master.target_component,
            *channels
        )
        print(f"🕹️ MAVLink: RC Override Sent (P:{pitch}, R:{roll}, T:{throttle}, Y:{yaw})")

if __name__ == "__main__":
    bridge = MAVLinkBridge()
    bridge.wait_for_heartbeat()
    
    try:
        while True:
            bridge.update()
            snapshot = bridge.get_snapshot()
            if int(time.time()) % 2 == 0: # Print every 2 seconds
                print(f"📦 Snapshot: {json.dumps(snapshot, indent=2)}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Bridge stopped.")
