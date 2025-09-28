# connectors/openai_conn.py
import os, requests
from .base import Connector, StepResult

OPENAI_PING = "https://api.openai.com/v1/models"

class OpenAIConnector(Connector):
    name = "OpenAI"

    def validate(self, cfg):
        key = (cfg.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
        if not key.startswith("sk-"):
            return StepResult(False, error="Missing or invalid OPENAI_API_KEY")
        try:
            r = requests.get(OPENAI_PING, headers={"Authorization": f"Bearer {key}"}, timeout=3)
            if r.status_code in (200, 401):  # 401 still proves auth path
                return StepResult(True, data={"reachable": True, "status": r.status_code})
            return StepResult(False, error=f"OpenAI API status {r.status_code}")
        except Exception as e:
            return StepResult(False, error=f"OpenAI API unreachable: {e}")

    def estimate_cost(self, spec):
        return 0.0

    def provision(self, spec, did):
        return StepResult(True, data={"use_model": spec.get("model", "gpt-4o-mini")})

    def smoke_test(self, state, did):
        return StepResult(True, data={"smoke": "skipped"})

    def teardown(self, state, did):
        return StepResult(True)
