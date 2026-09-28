"""Smoke-test the local assistant router against real analytics data."""
import sys, traceback
sys.path.insert(0, r"E:\AquaSense")

from backend.app.ai import intents, service as ai_svc

QUESTIONS = [
    "Which area consumes the most water?",
    "When is peak water consumption?",
    "Which area wastes the most water?",
    "How much water was wasted this month?",
    "Compare Hubballi Central and Vidyanagar",
    "Predict water consumption for the next 7 days",
    "What percentage of supplied water is wasted?",
    "What are the biggest anomalies?",
    "Show me the consumption trend for Vidyanagar",
    "What is the data quality?",
    "Who are the top consumers?",
    "Give me the dashboard summary",
    "What about pressure in the pipes?",
]

fails = 0
for q in QUESTIONS:
    try:
        result = ai_svc.answer(q)
        msg = result["message"].replace("\n", " ")[:110]
        tc = len(result.get("tool_calls", []))
        print(f"OK   [{result['mode']:5s}] tools={tc} :: {msg}")
    except Exception:
        fails += 1
        print(f"FAIL :: {q!r}")
        traceback.print_exc()

print(f"\n{fails} failures / {len(QUESTIONS)} questions")
sys.exit(1 if fails else 0)