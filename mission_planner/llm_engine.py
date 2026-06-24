import json
import re
import requests
from typing import Dict, Any, Tuple


class LLMEngine:

    def __init__(
        self,
        api_url: str = "http://localhost:11434/api/generate",
        model: str = "mistral"
    ):

        self.api_url = api_url
        self.model = model

        print(f"[PRANAVA] Using LLM model: {self.model}")

        # =====================================================
        # MINIMAL FAST SYSTEM PROMPT
        # =====================================================

        self.system_prompt = """
You are PRANAVA UAV mission planner.

Return ONLY valid JSON.

Supported mission types:
- grid
- spiral_in
- spiral_out
- waypoint

MISSION RULES:

GRID requires:
- area
- altitude
- passes
- direction
- points_per_pass
- speed (optional)

SPIRAL requires:
- area
- altitude
- loops
- points_per_loop
- speed (optional)

WAYPOINT requires:
- waypoints
- speed (optional)

CRITICAL JSON RULES:
- Output ONLY valid JSON
- No markdown
- No explanations
- No comments
- No extra text
- Coordinates MUST use JSON arrays
- NEVER use tuples

CORRECT:
"coordinates": [
  [15.36, 75.12],
  [15.37, 75.13]
]

WRONG:
"coordinates": [
  (15.36, 75.12),
  (15.37, 75.13)
]

GRID JSON FORMAT:

{
  "mission_type": "grid",
  "area": {
    "type": "polygon",
    "coordinates": [
      [15.3676, 75.1252],
      [15.3676, 75.1260],
      [15.3667, 75.1260],
      [15.3667, 75.1252]
    ]
  },
  "altitude": 20,
  "passes": 5,
  "direction": "horizontal",
  "points_per_pass": 5,
  "speed": 10
}

SPIRAL JSON FORMAT:

{
  "mission_type": "spiral_out",
  "area": {
    "type": "polygon",
    "coordinates": [
      [15.3676, 75.1252],
      [15.3676, 75.1260],
      [15.3667, 75.1260],
      [15.3667, 75.1252]
    ]
  },
  "altitude": 20,
  "loops": 4,
  "points_per_loop": 12,
  "speed": 8
}

WAYPOINT JSON FORMAT:

{
  "mission_type": "waypoint",
  "waypoints": [
    {
      "lat": 15.3676,
      "lon": 75.1252,
      "alt": 20
    },
    {
      "lat": 15.3678,
      "lon": 75.1260,
      "alt": 20
    }
  ],
  "speed": 5
}
"""

    # =========================================================
    # JSON EXTRACTION + AUTO-REPAIR
    # =========================================================

    def extract_json(self, text: str) -> Dict[str, Any]:

        match = re.search(r'\{.*\}', text, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found in LLM response.")

        json_text = match.group(0)

        # =====================================================
        # AUTO FIX TUPLE COORDINATES
        # =====================================================

        json_text = re.sub(
            r'\(([^()]*)\)',
            r'[\1]',
            json_text
        )

        # =====================================================
        # REMOVE TRAILING COMMAS
        # =====================================================

        json_text = re.sub(
            r',(\s*[}\]])',
            r'\1',
            json_text
        )

        # =====================================================
        # DEBUG PRINT
        # =====================================================

        print("\n========== RAW JSON ==========")
        print(json_text)
        print("================================\n")

        return json.loads(json_text)

    # =========================================================
    # MAIN CHAT FUNCTION
    # =========================================================

    def chat(self, user_input: str) -> Tuple[str, Dict[str, Any]]:

        prompt = f"""
{self.system_prompt}

USER REQUEST:
{user_input}

JSON RESPONSE:
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 256,
                "repeat_penalty": 1.05
            }
        }

        try:

            print("\n========== SENDING REQUEST ==========")
            print(user_input)
            print("=====================================\n")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=(10, 300)
            )

            response.raise_for_status()

            result = response.json()

            ai_msg = result.get("response", "").strip()

            print("\n========== RAW LLM RESPONSE ==========")
            print(ai_msg)
            print("======================================\n")

            mission_json = self.extract_json(ai_msg)

            return (
                "Mission parameters confirmed. Creating flight plan...",
                mission_json
            )

        except json.JSONDecodeError as e:

            return (
                f"JSON Parsing Error:\n{str(e)}",
                None
            )

        except requests.exceptions.Timeout:

            return (
                "LLM request timed out.\n"
                "The model is taking too long to respond.",
                None
            )

        except requests.exceptions.ConnectionError:

            return (
                "Unable to connect to Ollama.\n"
                "Please ensure Ollama is running locally.",
                None
            )

        except Exception as e:

            return (
                f"Error communicating with local LLM:\n{str(e)}",
                None
            )
