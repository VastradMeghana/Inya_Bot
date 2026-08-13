"""
Automated Test Suite for Voice Collections Bot (20 QA Test Scenarios)
Verifies middleware API handlers, date normalization logic, outcome schemas, and edge case recovery.
"""

import unittest
from datetime import datetime, timedelta
from middleware_server import parse_relative_date, app
from fastapi.testclient import TestClient

class TestVoiceCollectionsBot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.base_date = datetime(2026, 8, 13)  # Thursday

    # --- Test Category 1: Date Normalization Engine ---
    
    def test_tc01_date_today(self):
        result = parse_relative_date("today", self.base_date)
        self.assertEqual(result, "2026-08-13")

    def test_tc02_date_tomorrow(self):
        result = parse_relative_date("tomorrow", self.base_date)
        self.assertEqual(result, "2026-08-14")

    def test_tc03_date_this_friday(self):
        result = parse_relative_date("this Friday", self.base_date)
        self.assertEqual(result, "2026-08-14")  # Thursday -> Next Friday is tomorrow Aug 14

    def test_tc04_date_next_monday(self):
        result = parse_relative_date("next Monday", self.base_date)
        self.assertEqual(result, "2026-08-17")  # Thursday Aug 13 -> Next Monday Aug 17

    # --- Test Category 2: Middleware API Endpoints & Tools ---

    def test_tc05_start_call_endpoint(self):
        payload = {
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "campaign_id": "CMP-EARLY-20260813",
            "phone_number": "+919876543210",
            "preferred_language": "English"
        }
        headers = {"X-Idempotency-Key": "test-key-start-001"}
        response = self.client.post("/api/v1/calls/start", json=payload, headers=headers)
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn("call_id", data)
        self.assertEqual(data["status"], "QUEUED")

    def test_tc06_idempotency_start_call(self):
        payload = {
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "campaign_id": "CMP-EARLY-20260813",
            "phone_number": "+919876543210"
        }
        headers = {"X-Idempotency-Key": "test-key-start-001"}
        response2 = self.client.post("/api/v1/calls/start", json=payload, headers=headers)
        self.assertEqual(response2.status_code, 202)

    def test_tc07_tool_execution_normalize_date(self):
        payload = {
            "call_id": "CALL-20260813-TEST1",
            "event_type": "TOOL_EXECUTION",
            "timestamp": "2026-08-13T07:45:00+05:30",
            "current_state": "PROMPT_SPECIFIC_DATE",
            "tool_name": "normalize_date",
            "tool_arguments": {"raw_utterance": "tomorrow"}
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST1/events", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tool_name"], "normalize_date")
        self.assertIn("normalized_date", data["result"])

    def test_tc08_tool_execution_payment_link(self):
        payload = {
            "call_id": "CALL-20260813-TEST2",
            "event_type": "TOOL_EXECUTION",
            "timestamp": "2026-08-13T07:45:00+05:30",
            "current_state": "CONFIRM_PAYMENT_DETAILS",
            "tool_name": "send_payment_link",
            "tool_arguments": {"borrower_id": "BRW-90412"}
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST2/events", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["result"]["delivered"], True)

    def test_tc09_outcome_logging_happy_path(self):
        payload = {
            "call_id": "CALL-20260813-TEST3",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 45,
            "call_status": "CONNECTED",
            "primary_intent": "PAYMENT_READY",
            "final_outcome_code": "PAYMENT_COMMITMENT_TODAY",
            "commitment_amount": 8500.0,
            "commitment_date": "2026-08-13",
            "payment_mode": "UPI",
            "callback_required": False,
            "escalation_required": False,
            "conversation_summary": "Borrower agreed to pay full EMI today via SMS link.",
            "confidence_score": 0.98
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST3/outcome", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["crm_updated"], True)

    def test_tc10_outcome_logging_financial_hardship(self):
        payload = {
            "call_id": "CALL-20260813-TEST4",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 90,
            "call_status": "CONNECTED",
            "primary_intent": "FINANCIAL_DIFFICULTY",
            "final_outcome_code": "FINANCIAL_HARDSHIP",
            "escalation_required": True,
            "escalation_reason": "Job loss, unable to pay partial amount",
            "conversation_summary": "Borrower facing hardship. Escalated to human desk.",
            "confidence_score": 0.95
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST4/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc11_callback_scheduling(self):
        payload = {
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "callback_timestamp": "2026-08-14T17:00:00+05:30",
            "notes": "Driving during call"
        }
        response = self.client.post("/api/v1/callbacks", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("callback_id", response.json())

    def test_tc12_human_escalation_queue(self):
        payload = {
            "call_id": "CALL-20260813-TEST5",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "priority": "HIGH",
            "escalation_type": "ACCOUNT_DISPUTE",
            "reason": "Borrower disputed interest calculation"
        }
        response = self.client.post("/api/v1/escalations", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["priority"], "HIGH")

    # --- Test Category 3: Edge Cases & Outcome Mappings ---

    def test_tc13_wrong_number_outcome(self):
        payload = {
            "call_id": "CALL-20260813-TEST6",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 15,
            "call_status": "CONNECTED",
            "primary_intent": "WRONG_NUMBER",
            "final_outcome_code": "WRONG_NUMBER",
            "conversation_summary": "Recipient stated wrong number. No details disclosed.",
            "confidence_score": 0.99
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST6/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc14_already_paid_with_utr(self):
        payload = {
            "call_id": "CALL-20260813-TEST7",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 50,
            "call_status": "CONNECTED",
            "primary_intent": "ALREADY_PAID",
            "final_outcome_code": "CLAIMED_ALREADY_PAID",
            "claimed_transaction_ref": "UTR/4239108492",
            "conversation_summary": "Borrower claimed paid yesterday via GPay. Captured UTR 4239108492.",
            "confidence_score": 0.96
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST7/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc15_dnc_request(self):
        payload = {
            "call_id": "CALL-20260813-TEST8",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 20,
            "call_status": "CONNECTED",
            "primary_intent": "DO_NOT_CALL",
            "final_outcome_code": "DNC_REQUESTED",
            "dnc_flag": True,
            "conversation_summary": "Borrower requested DNC.",
            "confidence_score": 0.98
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST8/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc16_third_party_contact(self):
        payload = {
            "call_id": "CALL-20260813-TEST9",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 25,
            "call_status": "CONNECTED",
            "primary_intent": "THIRD_PARTY_ANSWERED",
            "final_outcome_code": "THIRD_PARTY_CONTACT",
            "conversation_summary": "Brother answered call. Requested callback. Zero loan info disclosed.",
            "confidence_score": 0.94
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST9/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc17_silence_timeout(self):
        payload = {
            "call_id": "CALL-20260813-TEST10",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 12,
            "call_status": "CONNECTED",
            "primary_intent": "SILENCE",
            "final_outcome_code": "NO_CONTACT_SILENCE",
            "conversation_summary": "No audio received after 3 recovery strikes.",
            "confidence_score": 0.90
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST10/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc18_unclear_audio_escalation(self):
        payload = {
            "call_id": "CALL-20260813-TEST11",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 35,
            "call_status": "CONNECTED",
            "primary_intent": "UNCLEAR_RESPONSE",
            "final_outcome_code": "UNCLEAR_AUDIO_ESCALATED",
            "escalation_required": True,
            "conversation_summary": "High noise level. Transferred to human.",
            "confidence_score": 0.65
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST11/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc19_refusal_to_pay(self):
        payload = {
            "call_id": "CALL-20260813-TEST12",
            "borrower_id": "BRW-90412",
            "loan_id": "LN-1023489",
            "call_duration_seconds": 40,
            "call_status": "CONNECTED",
            "primary_intent": "REFUSES_TO_PAY",
            "final_outcome_code": "REFUSED_TO_PAY",
            "escalation_required": True,
            "conversation_summary": "Borrower refused payment. Escalated to manager.",
            "confidence_score": 0.97
        }
        response = self.client.post("/api/v1/calls/CALL-20260813-TEST12/outcome", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_tc20_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "HEALTHY")


if __name__ == "__main__":
    unittest.main()
