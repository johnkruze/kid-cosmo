#!/usr/bin/env python3
"""
KID COSMO — Reasoning Agent v1.0
Generates structured Decision Manifests using local LLM inference.
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Attempt to import mlx_lm for Apple Silicon inference
try:
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

# Import model configuration
from model_config import get_model_path, MODEL_PROFILES

class ReasoningAgent:
    def __init__(self, model_path: str = None, profile: str = None):
        # Use model_config to resolve path from profile or environment
        self.model_path = model_path or get_model_path(profile)
        self.profile = profile or os.environ.get("KIDCOSMO_PROFILE", "fast")
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

        # Log which model is being used
        profile_info = MODEL_PROFILES.get(self.profile, {})
        print(f"🧠 ReasoningAgent initialized with profile: {self.profile}")
        print(f"   Model: {profile_info.get('name', self.model_path)}")

    def _load_model(self):
        if not HAS_MLX:
            print("MLX-LM not found. Reasoning will use fallback logic.")
            return

        if not self.is_loaded:
            print(f"Loading Reasoning Brain: {self.model_path}...")
            try:
                self.model, self.tokenizer = load(self.model_path)
                self.is_loaded = True
                print("Brain Loaded. Ready for Agentic Inference.")
            except Exception as e:
                print(f"Failed to load MLX model: {e}")
                self.is_loaded = False

    def generate_manifest(
        self,
        mission_id: str,
        environment: str,
        telemetry_snapshot: Dict[str, Any],
        anomaly_description: str,
        epistemic_isolation: bool = False,
        trajectory_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generates a structured Reasoning Manifest based on telemetry and anomaly."""
        timestamp = datetime.utcnow().isoformat() + "Z"

        if epistemic_isolation:
            print("DARK WINDOW DETECTED: Operating in epistemic isolation...")

        prompt = self._construct_prompt(mission_id, environment, telemetry_snapshot, anomaly_description, epistemic_isolation)
        reasoning_data = None

        if HAS_MLX and (self.is_loaded or self._load_model() or self.is_loaded):
            try:
                system_msg = "You are an expert autonomous pilot reasoning engine. Output ONLY raw JSON matching the requested schema."
                if epistemic_isolation:
                    system_msg += " CRITICAL: You are in a DARK WINDOW blackout. No external link. Rely solely on onboard sensors."

                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ]

                full_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                response_text = generate(self.model, self.tokenizer, prompt=full_prompt, max_tokens=1024, verbose=False)

                try:
                    if "```json" in response_text:
                        json_str = response_text.split("```json")[1].split("```")[0].strip()
                    else:
                        json_str = response_text.strip()
                    reasoning_data = json.loads(json_str)
                except Exception:
                    reasoning_data = self._generate_fallback_reasoning(anomaly_description, epistemic_isolation)
            except Exception as e:
                print(f"MLX Inference Error: {e}")
                reasoning_data = self._generate_fallback_reasoning(anomaly_description, epistemic_isolation)
        else:
            reasoning_data = self._generate_fallback_reasoning(anomaly_description, epistemic_isolation)

        manifest = {
            "mission_id": mission_id,
            "environment": environment,
            "timestamp": timestamp,
            "is_dark_window": epistemic_isolation,
            "telemetry_ref": f"{mission_id}_telemetry.json",
            "epistemic_status": "503_BLACKOUT" if epistemic_isolation else "NOMINAL_LINK",
            "agent_reasoning": reasoning_data,
            "trajectory_context": trajectory_context or {},
            "sha256_proof": ""
        }

        manifest_str = json.dumps(manifest, sort_keys=True)
        manifest["sha256_proof"] = hashlib.sha256(manifest_str.encode()).hexdigest()

        return manifest

    def _construct_prompt(self, mission_id: str, environment: str, telemetry: Dict[str, Any], anomaly: str, isolation: bool = False) -> str:
        context = "CRITICAL: You are isolated. No external link. Use somatic intuition." if isolation else ""

        return f"""
Analyze the following telemetry and anomaly. Generate a 'Reasoning Manifest' JSON object.
{context}

MISSION: {mission_id}
ENVIRONMENT: {environment}
ANOMALY: {anomaly}
TELEMETRY: {json.dumps(telemetry)}

REQUIRED JSON STRUCTURE:
{{
    "sensory_synthesis": {{
      "inputs": ["list", "of", "sensor", "alerts"],
      "interpretation": "narrative interpretation of sensors"
    }},
    "cognitive_load": 0.0-1.0,
    "internal_deliberation": [
      {{ "thought": "internal agent thought", "confidence": 0.0-1.0, "action_rejected": "string" }}
    ],
    "mission_assurance_check": {{
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
      "failure_mode_prediction": "prediction of what happens next",
      "mitigation_strategy": "what to do to fix it"
    }},
    "decision": {{
      "actuator_command": "command string",
      "expected_outcome": "what is expected"
    }},
    "self_reflection": "reflection on the event"
}}
"""

    def _generate_fallback_reasoning(self, anomaly: str, isolation: bool = False) -> Dict[str, Any]:
        context_str = "Isolated (Dark Window)" if isolation else "Nominal Link"
        return {
            "sensory_synthesis": {
                "inputs": ["ANOMALY_DETECTED", "TELEMETRY_VARIANCE_HIGH", "LINK_STATUS_BLACKOUT" if isolation else "LINK_STABLE"],
                "interpretation": f"[{context_str}] System detecting non-nominal state: {anomaly}. Sensors reporting divergence from expected trajectory."
            },
            "cognitive_load": 0.85,
            "internal_deliberation": [
                {
                    "thought": f"Trajectory exceeds 2-sigma deviation. {'No external link available.' if isolation else ''} Parameters may be compromised.",
                    "confidence": 0.90,
                    "action_rejected": "MAINTAIN_CURRENT_ATTITUDE"
                }
            ],
            "mission_assurance_check": {
                "risk_level": "HIGH",
                "failure_mode_prediction": "Potential uncontrolled drift or system degradation.",
                "mitigation_strategy": "Engage stabilization. Prioritize power conservation."
            },
            "decision": {
                "actuator_command": "HOLD_POSITION",
                "expected_outcome": "Maintain stability and wait for conditions to improve."
            },
            "self_reflection": f"Operating in {'epistemic isolation' if isolation else 'degraded mode'}. Physical intuition suggests conservative action."
        }

if __name__ == "__main__":
    agent = ReasoningAgent()
    test_snapshot = {"velocity": [500, 20, 10], "altitude": 4500, "attitude": [0.1, 0.5, 0.0]}
    test_manifest = agent.generate_manifest("TEST_MISSION", "TEST_ENV", test_snapshot, "Test anomaly detected.")
    print(json.dumps(test_manifest, indent=2))
