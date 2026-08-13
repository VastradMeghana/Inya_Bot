"""
NBFC Voice Collections Bot - Interactive Call Simulator
Simulates multi-turn voice conversations, state machine transitions, tool calls, and structured outcome logging.
"""

import sys
import json
from datetime import datetime, timedelta
from middleware_server import parse_relative_date, app
from fastapi.testclient import TestClient

client = TestClient(app)

BORROWER_CONTEXT = {
    "borrower_id": "BRW-90412",
    "borrower_name": "Rahul Sharma",
    "loan_id": "LN-1023489",
    "emi_amount": 8500,
    "due_date": "2026-08-10",
    "days_past_due": 3,
    "phone_number": "+919876543210",
    "preferred_language": "English",
    "minimum_partial_amount_allowed": 4250
}

DEMO_SCENARIOS = {
    "1": {
        "title": "Successful Immediate Payment Commitment (UPI SMS)",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "Yes, Rahul speaking."),
            ("Agent: Hi Rahul, calling from Apex NBFC. Your EMI of Rs. 8,500 was due on August 10th. May I know when you will pay?", "I can pay right now if you send the link.")
        ],
        "tool": "send_payment_link",
        "intent": "PAYMENT_READY",
        "outcome_code": "PAYMENT_COMMITMENT_TODAY",
        "amount": 8500,
        "date": datetime.now().strftime("%Y-%m-%d")
    },
    "2": {
        "title": "Payment Later - Relative Date Normalization",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "Yes."),
            ("Agent: Hi Rahul, calling from Apex NBFC regarding your pending EMI of Rs. 8,500 due on August 10th.", "I get my salary this Friday, I'll pay then.")
        ],
        "tool": "normalize_date",
        "raw_date": "this Friday",
        "intent": "PAYMENT_LATER",
        "outcome_code": "PAYMENT_COMMITMENT_FUTURE",
        "amount": 8500
    },
    "3": {
        "title": "Financial Difficulty - Empathy & Partial Payment",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "Yes."),
            ("Agent: Hi Rahul, calling from Apex NBFC about your pending EMI of Rs. 8,500.", "I lost my job last month, I have no money."),
            ("Agent: I'm sorry to hear that, Rahul. Would you be able to make a partial payment of Rs. 4,000 on Monday?", "Yes, I can manage Rs. 4,000 by Monday.")
        ],
        "intent": "PARTIAL_PAYMENT",
        "outcome_code": "PARTIAL_PAYMENT_COMMITMENT",
        "amount": 4000,
        "raw_date": "next Monday"
    },
    "4": {
        "title": "Wrong Number - Zero Data Leakage Privacy",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "No, wrong number. Rahul doesn't live here.")
        ],
        "intent": "WRONG_NUMBER",
        "outcome_code": "WRONG_NUMBER",
        "amount": None,
        "date": None
    },
    "5": {
        "title": "Claimed Already Paid - UTR Reference Capture",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "Yes."),
            ("Agent: Hi Rahul, calling regarding your pending EMI of Rs. 8,500.", "I already paid yesterday evening via UPI."),
            ("Agent: Thank you! Could you share the transaction reference number or UTR?", "Ref is UTR/4239108492.")
        ],
        "intent": "ALREADY_PAID",
        "outcome_code": "CLAIMED_ALREADY_PAID",
        "utr": "UTR/4239108492"
    },
    "6": {
        "title": "Human Escalation Request",
        "turns": [
            ("Agent: Hello, am I speaking with Rahul Sharma?", "Yes."),
            ("Agent: Hi Rahul, calling regarding your pending EMI of Rs. 8,500.", "Your penalty calculation is wrong. Connect me to a human manager.")
        ],
        "intent": "HUMAN_AGENT_REQUEST",
        "outcome_code": "HUMAN_AGENT_REQUESTED",
        "escalate": True
    }
}


def run_simulation(option: str):
    scenario = DEMO_SCENARIOS.get(option)
    if not scenario:
        print("Invalid option selected.")
        return

    print("\n" + "="*70)
    print(f"   RUNNING DEMO SCENARIO {option}: {scenario['title']}")
    print("="*70)
    print(f"Borrower Context: {json.dumps(BORROWER_CONTEXT, indent=2)}\n")

    # Step 1: Start Call Session
    start_resp = client.post("/api/v1/calls/start", json={
        "borrower_id": BORROWER_CONTEXT["borrower_id"],
        "loan_id": BORROWER_CONTEXT["loan_id"],
        "campaign_id": "CMP-DEMO-20260813",
        "phone_number": BORROWER_CONTEXT["phone_number"]
    }, headers={"X-Idempotency-Key": f"demo-sim-{option}"})

    call_id = start_resp.json()["call_id"]
    print(f" [OUTBOUND CALL LAUNCHED] Call ID: {call_id}")
    print("----------------------------------------------------------------------")

    # Step 2: Simulate Turns
    for agent_line, user_line in scenario["turns"]:
        print(f"  [BOT] {agent_line}")
        print(f"  [BORROWER] {user_line}\n")

    # Step 3: Middleware Tool Executions if needed
    date_val = scenario.get("date")
    if "raw_date" in scenario:
        raw_text = scenario["raw_date"]
        tool_evt = client.post(f"/api/v1/calls/{call_id}/events", json={
            "call_id": call_id,
            "event_type": "TOOL_EXECUTION",
            "timestamp": datetime.now().isoformat(),
            "current_state": "PROMPT_SPECIFIC_DATE",
            "tool_name": "normalize_date",
            "tool_arguments": {"raw_utterance": raw_text}
        })
        date_val = tool_evt.json()["result"]["normalized_date"]
        print(f" [TOOL EXECUTION] normalize_date('{raw_text}') -> Normalized: {date_val}")

    if scenario.get("tool") == "send_payment_link":
        tool_evt = client.post(f"/api/v1/calls/{call_id}/events", json={
            "call_id": call_id,
            "event_type": "TOOL_EXECUTION",
            "timestamp": datetime.now().isoformat(),
            "current_state": "CONFIRM_PAYMENT_DETAILS",
            "tool_name": "send_payment_link",
            "tool_arguments": {"borrower_id": BORROWER_CONTEXT["borrower_id"]}
        })
        print(f" [TOOL EXECUTION] send_payment_link -> Payment SMS Dispatched successfully")

    if scenario.get("escalate"):
        esc_resp = client.post("/api/v1/escalations", json={
            "call_id": call_id,
            "borrower_id": BORROWER_CONTEXT["borrower_id"],
            "loan_id": BORROWER_CONTEXT["loan_id"],
            "priority": "HIGH",
            "escalation_type": "USER_REQUEST",
            "reason": "Borrower requested human representative"
        })
        print(f" [HUMAN ESCALATION TRIGGERED] Escalation ID: {esc_resp.json()['escalation_id']}")

    # Step 4: Final Outcome Log
    outcome_payload = {
        "call_id": call_id,
        "borrower_id": BORROWER_CONTEXT["borrower_id"],
        "loan_id": BORROWER_CONTEXT["loan_id"],
        "call_duration_seconds": 45,
        "call_status": "CONNECTED",
        "primary_intent": scenario["intent"],
        "final_outcome_code": scenario["outcome_code"],
        "commitment_amount": scenario.get("amount"),
        "commitment_date": date_val,
        "claimed_transaction_ref": scenario.get("utr"),
        "callback_required": False,
        "escalation_required": scenario.get("escalate", False),
        "conversation_summary": f"Simulated call for scenario: {scenario['title']}",
        "confidence_score": 0.97
    }

    out_resp = client.post(f"/api/v1/calls/{call_id}/outcome", json=outcome_payload)

    print("----------------------------------------------------------------------")
    print(" [POST-CALL CRM OUTCOME LOGGED]")
    print(json.dumps(out_resp.json()["data"], indent=2))
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("#  VOICE COLLECTIONS BOT ON INYA - DEMO SIMULATOR")
    print("#"*70)
    
    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
        if choice.upper() == "A":
            for k in ["1", "2", "3", "4", "5", "6"]:
                run_simulation(k)
        else:
            run_simulation(choice)
    else:
        print("\nSelect a Demonstration Call Scenario:")
        for k, v in DEMO_SCENARIOS.items():
            print(f" [{k}] {v['title']}")
        print(" [A] Run ALL 6 Demo Scenarios sequentially")
        print(" [Q] Quit\n")

        inp = input("Enter choice (1-6 or A): ").strip()
        if inp.upper() == "A":
            for k in ["1", "2", "3", "4", "5", "6"]:
                run_simulation(k)
        elif inp in DEMO_SCENARIOS:
            run_simulation(inp)
        else:
            print("Exiting simulator.")
