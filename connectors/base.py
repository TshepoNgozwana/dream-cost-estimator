# connectors/base.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StepResult:
    ok: bool
    data: Dict[str, Any] | None = None
    error: str = ""

class Connector:
    name: str = "base"
    def validate(self, cfg: Dict[str, Any]) -> StepResult: ...
    def estimate_cost(self, spec: Dict[str, Any]) -> float: ...
    def provision(self, spec: Dict[str, Any], did: str) -> StepResult: ...
    def smoke_test(self, state: Dict[str, Any], did: str) -> StepResult: ...
    def teardown(self, state: Dict[str, Any], did: str) -> StepResult: ...
