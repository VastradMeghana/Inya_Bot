# Enterprise Voice Collections Bot on Inya Platform

> **Gnani FDE Competitive Assignment**  
> **Target Use Case**: Early-Stage Loan Collections (1–30 DPD) for a Mid-Sized NBFC  
> **Platform Engine**: Inya Agentic AI Voice Platform + FastAPI Middleware Gateway  
> **Status**: Production-Ready Blueprint, Web Simulator & Automated Test Suite (100% Pass)

---

## Executive Summary

This repository contains the complete technical architecture, conversational engine, system prompt, integration API specifications, and runnable test suite for an enterprise **Voice Collections Bot on the Inya platform**.

Designed for early-stage debt recovery (1–30 DPD), the solution balances **natural multi-turn voice interaction** with **strict deterministic business logic**, ensuring complete compliance with the RBI Fair Practice Code, zero privacy leakage, and hallucination-free financial disclosures.

---

## Key Solution Highlights

- **4-Tier Decoupled Architecture**: Voice Telephony (Inya) → NLU & Prompt Engine → Deterministic Middleware → NBFC Core Banking & CRM.
- **Zero-Knowledge Privacy Check**: Loan details are strictly protected until borrower identity is positively verified.
- **Dynamic Date & Amount Normalization**: Mid-call tool calls (`normalize_date`) parse relative dates (*"this Friday"*, *"next Monday"*) into canonical `YYYY-MM-DD` formats.
- **Empathy & Partial Payment Negotiation**: Structured hardship flow offering automated partial EMI options (e.g. 50% threshold) before warm escalation.
- **100% Safe Escalation Routing**: Immediate transfer to human specialists for disputes, fraud claims, severe hardship, or DNC requests.
- **Production Idempotency & Resiliency**: Network retries enforce `X-Idempotency-Key` headers with AWS SQS Dead Letter Queue (DLQ) fallback.

---

## 📁 Repository File Structure

```text
c:\Users\Meghana Vastrad\Desktop\gnani.ai\
├── README.md                      # Complete Project Documentation & Evaluation Guide
├── middleware_server.py           # FastAPI REST Middleware & Interactive Web Demo UI
├── simulator.py                   # CLI Interactive Call Simulator for 6 Key Scenarios
├── test_suite.py                  # Automated QA Test Runner (20 QA Test Cases)
├── borrower_data_model.json       # Three-phase Borrower Data Schema (Pre, Mid, Post)
├── system_prompt.md               # Enterprise Production System Prompt Engine
├── dialogue_scripts.md            # Voice-optimized Natural Phone Dialogue Scripts
├── objection_handling.md          # Multi-turn Objection & Escalation Handling Matrix
├── outcome_schema.json            # Post-Call Structured Outcome Extraction JSON Schema
├── api_specification.md           # REST API Specs (POST /calls/start, /events, /outcome)
└── qa_test_suite_and_demo.md      # 20 QA Test Scenarios Matrix & 6 Demo Call Scripts
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              1. TELEPHONY & VOICE LAYER                 │
│  Inya Voice Gateway: SIP/PSTN | ASR | TTS | VAD/Barge-in│
└──────────────────────────┬──────────────────────────────┘
                           │ Audio / Speech Stream
┌──────────────────────────▼──────────────────────────────┐
│           2. AGENTIC & CONVERSATIONAL LAYER             │
│   Inya System Prompt | Intent Classifier | State Tracker│
└──────────────────────────┬──────────────────────────────┘
                           │ Synchronous Tool Calls / Webhooks (500ms SLA)
┌──────────────────────────▼──────────────────────────────┐
│          3. DETERMINISTIC MIDDLEWARE LAYER              │
│  Date Normalizer | Partial Payment Rules | Compliance   │
└──────────────────────────┬──────────────────────────────┘
                           │ Idempotent REST APIs (X-Idempotency-Key)
┌──────────────────────────▼──────────────────────────────┐
│          4. CORE BACKEND & INTEGRATION LAYER            │
│    Collections CRM | LMS | Audit Log DB | Escalations   │
└────────────────────────## Quick Start & Local Execution Guide

### Prerequisites
- **Python**: 3.10 or higher installed on your system.
- **Dependencies**: `fastapi`, `uvicorn`, `pydantic`.

### Installation
Open terminal in the project directory:
```bash
cd "c:\Users\Meghana Vastrad\Desktop\gnani.ai"
pip install fastapi uvicorn pydantic
```

---

### 1. Launch the Live Middleware Server & Web Demo UI
Run the FastAPI middleware server:
```bash
python middleware_server.py
```

Once running, access the following URLs in your browser:
- 🌐 **Interactive Web Call Simulator**: [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)
- 📚 **Swagger REST API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🏥 **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 2. Run the 20-Scenario Automated Unit Test Suite
Execute the automated QA test suite verifying all state transitions, date conversions, tool executions, and outcome mappings:
```bash
python test_suite.py
```
**Expected Output**: `Ran 20 tests in 0.245s -> OK (100% Pass)`

---

### 3. Run the CLI Call Simulator
Simulate multi-turn voice calls directly in your terminal:
```bash
python simulator.py A
```
*(Or specify individual scenario numbers: `python simulator.py 1` through `python simulator.py 6`)*

---

## 🎯 Intent Taxonomy (20 Intent Specifications)

| Intent Name | Utterance Example | Required Extracted Fields | Next State | Final Outcome Code |
| :--- | :--- | :--- | :--- | :--- |
| `PAYMENT_READY` | *"I can pay right now via UPI"* | `payment_channel` | `CONFIRM_PAYMENT_DETAILS` | `PAYMENT_COMMITMENT_TODAY` |
| `PAYMENT_LATER` | *"I will pay this Friday"* | `commitment_date`, `amount` | `ASK_EXPECTED_DATE` | `PAYMENT_COMMITMENT_FUTURE` |
| `FINANCIAL_DIFFICULTY` | *"Salary delayed, no money now"* | `reason`, `partial_amount` | `EXPLORE_PARTIAL_PAYMENT` | `FINANCIAL_HARDSHIP` |
| `CALLBACK_REQUEST` | *"I am driving, call after 5 PM"* | `callback_date`, `time` | `CAPTURE_CALLBACK_SLOT` | `CALLBACK_SCHEDULED` |
| `WRONG_NUMBER` | *"Wrong number, no Rahul lives here"*| `is_wrong_number` | `STOP_LOAN_DISCLOSURE` | `WRONG_NUMBER` |
| `BORROWER_DENIES_LOAN` | *"I never took any loan"* | `denial_reason` | `LOG_DISPUTE` | `LOAN_DISOWNED_DISPUTE` |
| `ALREADY_PAID` | *"I paid yesterday via GPay"* | `payment_date`, `utr` | `CAPTURE_PAYMENT_DETAILS` | `CLAIMED_ALREADY_PAID` |
| `PARTIAL_PAYMENT` | *"I can only pay ₹4,000 today"* | `partial_amount` | `CONFIRM_PARTIAL_AMOUNT` | `PARTIAL_PAYMENT_COMMITMENT` |
| `FULL_PAYMENT_COMMITMENT`| *"Will pay full ₹8,500 on 15th"* | `amount`, `date` | `CONFIRM_COMMITMENT` | `FULL_PAYMENT_COMMITMENT` |
| `REFUSES_TO_PAY` | *"I am not paying, do whatever"* | `refusal_reason` | `EVALUATE_REFUSAL` | `REFUSED_TO_PAY` |
| `NEEDS_PAYMENT_INFO` | *"How do I pay? Send link"* | `info_type` | `PROVIDE_PAYMENT_LINK` | `PAYMENT_INFO_PROVIDED` |
| `DISPUTE` | *"Penalty added unfairly"* | `dispute_category` | `LOG_DISPUTE` | `ACCOUNT_DISPUTE_ESCALATED` |
| `HUMAN_AGENT_REQUEST` | *"Connect me to a real person"* | `reason` | `TRANSFER_HUMAN` | `HUMAN_AGENT_REQUESTED` |
| `LANGUAGE_CHANGE` | *"Hindi me baat karo"* | `target_language` | `SWITCH_LANGUAGE_STATE` | `LANGUAGE_SWITCHED` |
| `DO_NOT_CALL` | *"Put me on DNC list"* | `dnc_type` | `LOG_DNC_PREFERENCE` | `DNC_REQUESTED` |
| `THIRD_PARTY_ANSWERED` | *"Rahul is out, I am his brother"*| `relation` | `HANDLE_THIRD_PARTY` | `THIRD_PARTY_CONTACT` |
| `BORROWER_UNAVAILABLE` | *"He is in a meeting"* | `availability_time` | `CAPTURE_CALLBACK_SLOT` | `BORROWER_UNAVAILABLE` |
| `SILENCE` | *Silence after 3 strikes* | N/A | `FALLBACK_RECOVERY` | `NO_CONTACT_SILENCE` |
| `UNCLEAR_RESPONSE` | Low confidence ASR | N/A | `FALLBACK_RECOVERY` | `UNCLEAR_AUDIO_ESCALATED` |
| `SYSTEM_ERROR` | API Gateway Timeout | `error_code` | `GRACEFUL_DISCONNECT` | `SYSTEM_ERROR_ESCALATED` |

---

## 🛠️ Inya Platform Setup & Configuration

1. **System Prompt Deployment**: Copy [system_prompt.md](file:///c:/Users/Meghana%20Vastrad/Desktop/gnani.ai/system_prompt.md) into the Inya Agent System Prompt settings.
2. **Context Variable Mapping**: Map pre-call campaign parameters: `{{borrower.borrower_name}}`, `{{borrower.emi_amount}}`, `{{borrower.due_date}}`, `{{borrower.loan_id}}`.
3. **Action Webhook Registration**:
   - `normalize_date` → `POST /api/v1/calls/{call_id}/events`
   - `send_payment_link` → `POST /api/v1/calls/{call_id}/events`
   - `schedule_callback` → `POST /api/v1/callbacks`
   - `escalate_human` → `POST /api/v1/escalations`
   - `log_outcome` → `POST /api/v1/calls/{call_id}/outcome`
4. **Post-Call Schema Enforcement**: Paste [outcome_schema.json](file:///c:/Users/Meghana%20Vastrad/Desktop/gnani.ai/outcome_schema.json) into Inya Structured Extraction configuration.
5. **Telephony Parameters**: Set Voice Activity Detection (VAD) silence threshold to **600ms** and Barge-in interruption sensitivity to **High (<200ms)**.

---

## 🔒 Security, Compliance & Observability

- **RBI Fair Practice Code**: Strict adherence — no aggressive language, no threats, no calling outside permissible hours.
- **Data Privacy & DPDP**: Zero debt disclosure to third parties or before identity confirmation.
- **Idempotency**: All state updates require `X-Idempotency-Key` headers to prevent duplicate payment link generation or duplicate CRM outcome entries.
- **Audit Logging**: Asynchronous dual-channel event stream recorded for every call turn with exact timestamps and ASR confidence scores.

---

## 🏆 Key Evaluation Metrics Supported

- **Contact Rate & Completion Rate**
- **Payment Commitment Rate & Fulfillment Rate**
- **Wrong-Number Flagging Rate & Privacy Compliance**
- **Human Escalation Rate & Intent Classification Accuracy**
- **Middleware API Latency (<500ms SLA)**
