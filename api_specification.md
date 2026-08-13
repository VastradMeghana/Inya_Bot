# Voice Collections Agent - Integration Architecture & REST API Specification

Enterprise backend integration design connecting the Inya Voice Agent with NBFC Core Banking (LMS) and Collections CRM.

---

## 1. INTEGRATION ARCHITECTURE

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   INYA VOICE    │       │   MIDDLEWARE    │       │ COLLECTIONS CRM │       │ CORE LMS / BANK │
│     GATEWAY     │──────►│   API GATEWAY   │──────►│  & TASK QUEUE   │──────►│   DATABASE      │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
         │                         │                         │                         │
         │-- POST /calls/start ----│                         │                         │
         │                         │-- Fetch Borrower Context│                         │
         │                         │◄------------------------│                         │
         │◄-- Launch Session ------│                         │                         │
         │                         │                         │                         │
         │-- POST /calls/{id}/evts-│ (State & Tool Exec)     │                         │
         │-- POST /calls/{id}/out--│                         │                         │
         │                         │-- Update CRM Record ----│                         │
         │                         │-- Trigger SMS Gateway --│                         │
         │                         │-- Queue Escalation Ticket------------------------►│
```

---

## 2. COMMON HTTP HEADERS & COMPLIANCE RULES

All API calls must enforce:
- **Authorization**: `Bearer <JWT_TOKEN>` (HMAC-SHA256 signed with 15-min expiration)
- **Content-Type**: `application/json`
- **Idempotency Key**: `X-Idempotency-Key: <UUIDv4>` (Ensures network retries do not duplicate outcomes or payment link dispatches)
- **Timeouts**: Real-time tool calls timeout at **500ms**; post-call CRM sync timeouts at **3000ms**.

---

## 3. ENDPOINT SPECIFICATIONS

### 3.1 POST /calls/start
Trigger an outbound collections call session for a target borrower.

#### Request Header
```http
POST /api/v1/calls/start HTTP/1.1
Host: api.collections.nbfc.com
Authorization: Bearer eyJhbGciOiJIUzI1Ni...
Content-Type: application/json
X-Idempotency-Key: 7b9e4a12-8c4d-4e9a-9d21-4f8101a91e01
```

#### Request Payload
```json
{
  "borrower_id": "BRW-90412",
  "loan_id": "LN-1023489",
  "campaign_id": "CMP-EARLY-20260813",
  "phone_number": "+919876543210",
  "preferred_language": "English",
  "max_call_duration_seconds": 180
}
```

#### Response (202 Accepted)
```json
{
  "call_id": "CALL-20260813-89012",
  "status": "QUEUED",
  "borrower_id": "BRW-90412",
  "created_at": "2026-08-13T07:45:00+05:30",
  "inyasession_token": "sess_89012_abc123xyz"
}
```

---

### 3.2 POST /calls/{call_id}/events
Stream real-time mid-call execution events and tool calls.

#### Request Payload (Tool Execution: Normalize Date)
```json
{
  "call_id": "CALL-20260813-89012",
  "event_type": "TOOL_EXECUTION",
  "timestamp": "2026-08-13T07:45:42+05:30",
  "current_state": "PROMPT_SPECIFIC_DATE",
  "tool_name": "normalize_date",
  "tool_arguments": {
    "raw_utterance": "this coming Friday",
    "reference_date": "2026-08-13"
  }
}
```

#### Response (200 OK)
```json
{
  "status": "SUCCESS",
  "tool_name": "normalize_date",
  "result": {
    "normalized_date": "2026-08-15",
    "is_valid_due_window": true
  }
}
```

---

### 3.3 POST /calls/{call_id}/outcome
Persist final structured outcome and conversation summary upon call completion.

#### Request Payload
```json
{
  "call_id": "CALL-20260813-89012",
  "borrower_id": "BRW-90412",
  "loan_id": "LN-1023489",
  "call_duration_seconds": 68,
  "call_status": "CONNECTED",
  "primary_intent": "PAYMENT_LATER",
  "final_outcome_code": "PAYMENT_COMMITMENT_FUTURE",
  "commitment_amount": 8500,
  "commitment_date": "2026-08-15",
  "payment_mode": "UPI",
  "callback_required": false,
  "escalation_required": false,
  "dnc_flag": false,
  "language_used": "English",
  "conversation_summary": "Verified borrower identity. Informed of overdue EMI ₹8,500. Borrower committed to paying full amount on August 15, 2026 via UPI SMS link.",
  "confidence_score": 0.96
}
```

#### Response (200 OK)
```json
{
  "status": "SUCCESS",
  "call_id": "CALL-20260813-89012",
  "crm_updated": true,
  "lms_updated": true,
  "processed_at": "2026-08-13T07:46:12+05:30"
}
```

---

### 3.4 POST /callbacks
Schedule borrower callback in CRM dialer queue.

#### Request Payload
```json
{
  "borrower_id": "BRW-90412",
  "loan_id": "LN-1023489",
  "callback_timestamp": "2026-08-14T17:00:00+05:30",
  "requested_by": "BORROWER",
  "notes": "Borrower driving during call. Requested callback after 5 PM."
}
```

---

### 3.5 POST /escalations
Queue immediate ticket for human collection specialist / hardship team.

#### Request Payload
```json
{
  "call_id": "CALL-20260813-89012",
  "borrower_id": "BRW-90412",
  "loan_id": "LN-1023489",
  "priority": "HIGH",
  "escalation_type": "FINANCIAL_HARDSHIP",
  "reason": "Borrower lost job, unable to pay full or minimum partial EMI.",
  "agent_transfer_attempted": false
}
```

---

## 4. ERROR HANDLING & RETRY POLICY

- **Standard RFC 7807 Error Response**:
```json
{
  "type": "https://api.collections.nbfc.com/errors/idempotency-conflict",
  "title": "Conflict",
  "status": 409,
  "detail": "An outcome for call_id CALL-20260813-89012 has already been logged.",
  "instance": "/api/v1/calls/CALL-20260813-89012/outcome"
}
```

- **Retry Strategy**:
  - CRM outcome posts retry **3 times** using exponential backoff (1s, 2s, 4s).
  - If CRM API remains unavailable, outcome payload is routed to an **AWS SQS Dead Letter Queue (DLQ)** for batch recovery, ensuring 100% data durability.
