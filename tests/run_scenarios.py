"""
Run with (from the NextStep/ project root):

    python -m tests.run_scenarios
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.agent import NextStepAgent
from tests.scenarios import SCENARIOS

agent = NextStepAgent()
all_results = []

for scenario in SCENARIOS:
    session_id = f"scenario-{scenario['id']}"
    print(f"\n=== Scenario {scenario['id']}: {scenario['type']} ===")
    result = agent.run(scenario["text"], session_id=session_id)
    print(json.dumps(result, indent=2, default=str))
    all_results.append({"scenario": scenario, "result": result})

out_path = os.path.join(os.path.dirname(__file__), "results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, default=str, ensure_ascii=False)
print(f"\nSaved results to {out_path}")