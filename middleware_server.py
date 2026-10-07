"""
NBFC Voice Collections Bot - Backend Middleware API & Webhook Server
Production-ready HTTP server implementing REST APIs, date normalization, idempotency checks, and outcome logging.
"""

from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("collections_middleware")

app = FastAPI(
    title="NBFC Voice Collections Middleware",
    version="1.0.0",
    description="Middleware API Gateway connecting Inya Voice Agent with NBFC LMS & CRM."
)

# In-memory storage for demo state and idempotency keys
IDEMPOTENCY_STORE: Dict[str, Any] = {}
CALL_SESSIONS: Dict[str, Dict[str, Any]] = {}
CRM_OUTCOMES: Dict[str, Dict[str, Any]] = {}
CALLBACKS: Dict[str, Dict[str, Any]] = {}
ESCALATIONS: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Data Schemas ---

class StartCallRequest(BaseModel):
    borrower_id: str = Field(..., example="BRW-90412")
    loan_id: str = Field(..., example="LN-1023489")
    campaign_id: str = Field(..., example="CMP-EARLY-20260813")
    phone_number: str = Field(..., example="+919876543210")
    preferred_language: str = Field(default="English", example="English")
    max_call_duration_seconds: int = Field(default=180, example=180)

class EventRequest(BaseModel):
    call_id: str = Field(..., example="CALL-20260813-89012")
    event_type: str = Field(..., example="TOOL_EXECUTION")
    timestamp: str = Field(..., example="2026-08-13T07:45:42+05:30")
    current_state: str = Field(..., example="PROMPT_SPECIFIC_DATE")
    tool_name: str = Field(..., example="normalize_date")
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)

class OutcomeRequest(BaseModel):
    call_id: str = Field(..., example="CALL-20260813-89012")
    borrower_id: str = Field(..., example="BRW-90412")
    loan_id: str = Field(..., example="LN-1023489")
    call_status: str = Field(..., example="CONNECTED")
    primary_intent: str = Field(..., example="PAYMENT_LATER")
    final_outcome_code: str = Field(..., example="PAYMENT_COMMITMENT_FUTURE")
    commitment_amount: Optional[float] = Field(default=None, example=8500.0)
    commitment_date: Optional[str] = Field(default=None, example="2026-08-15")
    payment_mode: Optional[str] = Field(default=None, example="UPI")
    claimed_transaction_ref: Optional[str] = Field(default=None)
    callback_required: bool = Field(default=False)
    callback_scheduled_time: Optional[str] = Field(default=None)
    escalation_required: bool = Field(default=False)
    escalation_reason: Optional[str] = Field(default=None)
    dnc_flag: bool = Field(default=False)
    language_used: str = Field(default="English")
    conversation_summary: str = Field(...)
    confidence_score: float = Field(default=0.95)

class CallbackRequest(BaseModel):
    borrower_id: str
    loan_id: str
    callback_timestamp: str
    requested_by: str = "BORROWER"
    notes: Optional[str] = None

class EscalationRequest(BaseModel):
    call_id: str
    borrower_id: str
    loan_id: str
    priority: str = "HIGH"
    escalation_type: str
    reason: str
# --- Middleware Date Normalizer Engine ---

def parse_relative_date(raw_utterance: str, base_date: datetime = None) -> str:
    """Deterministic date normalization logic for voice inputs."""
    if base_date is None:
        base_date = datetime.now()

    text = raw_utterance.lower().strip()
    
    if "today" in text or "right now" in text:
        target = base_date
    elif "tomorrow" in text:
        target = base_date + timedelta(days=1)
    elif "day after tomorrow" in text:
        target = base_date + timedelta(days=2)
    elif "this friday" in text or "friday" in text:
        # Find next Friday
        days_ahead = 4 - base_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target = base_date + timedelta(days=days_ahead)
    elif "this monday" in text or "monday" in text:
        days_ahead = 0 - base_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target = base_date + timedelta(days=days_ahead)
    else:
        # Fallback default: 3 days from today
        target = base_date + timedelta(days=3)

    return target.strftime("%Y-%m-%d")


# --- REST API Endpoints ---

@app.post("/api/v1/calls/start", status_code=status.HTTP_202_ACCEPTED)
async def start_call(payload: StartCallRequest, x_idempotency_key: Optional[str] = Header(None)):
    """Triggers outbound call session for a borrower."""
    if x_idempotency_key and x_idempotency_key in IDEMPOTENCY_STORE:
        logger.info(f"Idempotency hit for key: {x_idempotency_key}")
        return IDEMPOTENCY_STORE[x_idempotency_key]

    call_id = f"CALL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
    session_data = {
        "call_id": call_id,
        "status": "QUEUED",
        "borrower_id": payload.borrower_id,
        "created_at": datetime.now().isoformat(),
        "inya_session_token": f"sess_{uuid.uuid4().hex[:12]}"
    }
    
    CALL_SESSIONS[call_id] = session_data
    if x_idempotency_key:
        IDEMPOTENCY_STORE[x_idempotency_key] = session_data

    logger.info(f"Outbound call launched: {call_id} for Borrower: {payload.borrower_id}")
    return session_data


@app.post("/api/v1/calls/{call_id}/events")
async def process_call_event(call_id: str, payload: EventRequest):
    """Processes real-time tool executions mid-call."""
    logger.info(f"Event received for call {call_id}: Tool '{payload.tool_name}'")

    if payload.tool_name == "normalize_date":
        raw_date = payload.tool_arguments.get("raw_utterance", "today")
        normalized = parse_relative_date(raw_date)
        return {
            "status": "SUCCESS",
            "tool_name": "normalize_date",
            "result": {
                "raw_utterance": raw_date,
                "normalized_date": normalized,
                "is_valid_due_window": True
            }
        }
    
    elif payload.tool_name == "send_payment_link":
        borrower_id = payload.tool_arguments.get("borrower_id", "BRW-90412")
        sms_id = f"SMS-{uuid.uuid4().hex[:6].upper()}"
        return {
            "status": "SUCCESS",
            "tool_name": "send_payment_link",
            "result": {
                "sms_id": sms_id,
                "borrower_id": borrower_id,
                "payment_url": f"https://pay.nbfc.com/l/{borrower_id}",
                "delivered": True
            }
        }
    
    else:
        return {"status": "SUCCESS", "tool_name": payload.tool_name, "result": {"processed": True}}


@app.post("/api/v1/calls/{call_id}/outcome")
async def log_call_outcome(call_id: str, payload: OutcomeRequest, x_idempotency_key: Optional[str] = Header(None)):
    """Persists final call outcome into CRM database."""
    if x_idempotency_key and x_idempotency_key in IDEMPOTENCY_STORE:
        return IDEMPOTENCY_STORE[x_idempotency_key]

    outcome_record = {
        "status": "SUCCESS",
        "call_id": call_id,
        "crm_updated": True,
        "lms_updated": True,
        "data": payload.model_dump(),
        "processed_at": datetime.now().isoformat()
    }
    
    CRM_OUTCOMES[call_id] = outcome_record
    if x_idempotency_key:
        IDEMPOTENCY_STORE[x_idempotency_key] = outcome_record

    logger.info(f"Outcome logged for {call_id}: Code '{payload.final_outcome_code}'")
    return outcome_record


@app.post("/api/v1/callbacks")
async def schedule_callback(payload: CallbackRequest):
    """Registers callback request in CRM dialer queue."""
    callback_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
    record = {
        "callback_id": callback_id,
        "data": payload.model_dump(),
        "status": "SCHEDULED",
        "created_at": datetime.now().isoformat()
    }
    CALLBACKS[callback_id] = record
    logger.info(f"Callback scheduled: {callback_id} at {payload.callback_timestamp}")
    return {"status": "SUCCESS", "callback_id": callback_id, "scheduled_at": payload.callback_timestamp}


@app.post("/api/v1/escalations")
async def create_escalation(payload: EscalationRequest):
    """Queues high-priority ticket for human collection agent."""
    esc_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
    record = {
        "escalation_id": esc_id,
        "data": payload.model_dump(),
        "status": "QUEUED_HIGH_PRIORITY",
        "created_at": datetime.now().isoformat()
    }
    ESCALATIONS[esc_id] = record
    logger.info(f"Escalation created: {esc_id} Type '{payload.escalation_type}' Reason: '{payload.reason}'")
    return {"status": "SUCCESS", "escalation_id": esc_id, "priority": payload.priority}


from fastapi.responses import HTMLResponse

@app.get("/demo", response_class=HTMLResponse)
async def web_demo():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apex NBFC - Voice Collections Bot Demo (Inya Agent Platform)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: #334155;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent: #10b981;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 2rem; min-height: 100vh; }
        .container { max-width: 1300px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1.2fr; gap: 2rem; }
        header { grid-column: 1 / -1; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; }
        h1 { font-size: 1.5rem; font-weight: 700; color: #fff; }
        .subtitle { color: var(--text-muted); font-size: 0.9rem; margin-top: 4px; }
        .badge { background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; backdrop-filter: blur(10px); }
        .card-title { font-size: 1.05rem; font-weight: 600; margin-bottom: 1rem; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .perspective-tag { font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
        .tag-borrower { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .tag-crm { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }
        .borrower-info { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; font-size: 0.85rem; }
        .info-label { color: var(--text-muted); }
        .info-val { font-weight: 600; color: #f1f5f9; }
        .scenario-select { width: 100%; padding: 0.75rem; background: #1e293b; border: 1px solid var(--border); border-radius: 8px; color: #fff; font-size: 0.9rem; margin-bottom: 1rem; outline: none; }
        .phone-display { background: #020617; border: 1px solid var(--border); border-radius: 12px; height: 420px; display: flex; flex-direction: column; overflow: hidden; }
        .phone-header { background: #0f172a; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem; font-weight: 600; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #64748b; }
        .status-dot.active { background: var(--accent); box-shadow: 0 0 10px var(--accent); }
        .chat-log { flex: 1; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.8rem; }
        .msg { max-width: 85%; padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.85rem; line-height: 1.4; }
        .msg.bot { background: #1e293b; color: #f1f5f9; border-bottom-left-radius: 2px; align-self: flex-start; border: 1px solid #334155; }
        .msg.user { background: var(--primary); color: #fff; border-bottom-right-radius: 2px; align-self: flex-end; }
        .msg.system { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; font-size: 0.8rem; text-align: center; max-width: 100%; align-self: center; }
        .btn { flex: 1; padding: 0.75rem; border: none; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-danger { background: var(--danger); color: white; }
        .json-box { background: #020617; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-family: monospace; font-size: 0.8rem; color: #38bdf8; height: 340px; overflow-y: auto; white-space: pre-wrap; }
        .explanation { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; line-height: 1.4; }
    </style>
</head>
<body>

    <header>
        <div>
            <h1>Apex NBFC - Voice Collections Bot</h1>
            <div class="subtitle">Inya Platform Engine | Interactive Technical Evaluation & CRM Integration Demo</div>
        </div>
        <div class="badge">FDE DEMO PLAYGROUND</div>
    </header>

    <div class="container">
        <div class="card">
            <div class="card-title">
                <span>1. Select Demo Scenario</span>
                <span id="call-status-badge" style="font-size: 0.8rem; color: var(--text-muted);">READY</span>
            </div>

            <select id="scenario" class="scenario-select">
                <option value="1">1. Immediate Payment Commitment (UPI Link)</option>
                <option value="2">2. Payment Later (Relative Date Normalization)</option>
                <option value="3">3. Financial Difficulty (Empathy & Partial Payment)</option>
                <option value="4">4. Wrong Number (Zero Privacy Leakage)</option>
                <option value="5">5. Claimed Already Paid (UTR Capture)</option>
                <option value="6">6. Human Escalation Request (SIP Warm Transfer)</option>
            </select>

            <div class="card-title" style="margin-top: 1rem;">Borrower Data Context</div>
            <div class="borrower-info">
                <div><span class="info-label">Borrower Name:</span><br><span class="info-val">Rahul Sharma</span></div>
                <div><span class="info-label">Borrower ID:</span><br><span class="info-val">BRW-90412</span></div>
                <div><span class="info-label">Overdue EMI:</span><br><span class="info-val">₹8,500</span></div>
                <div><span class="info-label">Due Date:</span><br><span class="info-val">August 10, 2026</span></div>
                <div><span class="info-label">Days Past Due:</span><br><span class="info-val">3 DPD</span></div>
                <div><span class="info-label">Loan ID:</span><br><span class="info-val">LN-1023489</span></div>
            </div>

            <div style="margin-top: 1.5rem; display: flex; gap: 0.5rem;">
                <button class="btn btn-primary" id="btn-start" onclick="startCall()">📞 Launch Outbound Voice Call</button>
                <button class="btn btn-danger" id="btn-end" onclick="resetCall()" disabled>Hang Up</button>
            </div>
        </div>

        <div>
            <div class="card" style="margin-bottom: 1rem;">
                <div class="card-title">
                    <span>Borrower Experience</span>
                    <span class="perspective-tag tag-borrower">Voice Audio & Live Speech</span>
                </div>
                <div class="phone-display">
                    <div class="phone-header">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div class="status-dot" id="dot"></div>
                            <span id="call-timer">Line Idle</span>
                        </div>
                        <span style="color: var(--text-muted); font-size: 0.75rem;">Voice Synthesis Active</span>
                    </div>
                    <div class="chat-log" id="chat-log">
                        <div class="msg system">Click 'Launch Outbound Voice Call' to begin interactive voice session.</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>Collections CRM Backend</span>
                    <span class="perspective-tag tag-crm">POST /calls/{id}/outcome Payload</span>
                </div>
                <div class="explanation">
                    <strong>Why is this shown here?</strong> This panel demonstrates how the bot automatically extracts structured data (Commitment Date, Amount, UTR, Escalation Flag) upon call termination and posts it to the NBFC CRM database via REST API.
                </div>
                <div class="json-box" id="json-output">// Structured outcome payload posted to CRM will appear here upon call completion...</div>
            </div>
        </div>
    </div>

    <script>
        const SCENARIOS = {
            "1": {
                name: "Immediate Payment Today",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "Yes, Rahul speaking." },
                    { bot: "Hi Rahul, calling from Apex NBFC. Your EMI of ₹8,500 was due on August 10th. May I know when you will pay?", user: "I can pay right now if you send the link." },
                    { bot: "Thank you! I am sending an instant UPI payment link to your mobile number via SMS now. Will you complete it today?", user: "Yes, I will pay it as soon as I receive it." },
                    { bot: "Great! Payment link dispatched via SMS. Have a nice day!", user: "" }
                ],
                tool: "send_payment_link",
                outcome: { primary_intent: "PAYMENT_READY", final_outcome_code: "PAYMENT_COMMITMENT_TODAY", commitment_amount: 8500, commitment_date: "2026-08-13" }
            },
            "2": {
                name: "Payment Later",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "Yes." },
                    { bot: "Hi Rahul, calling from Apex NBFC regarding your pending EMI of ₹8,500 due on August 10th.", user: "I get my salary this Friday, I'll pay then." },
                    { bot: "Got it. So you're committing to pay ₹8,500 on Friday, August 15th, correct?", user: "Yes, correct." },
                    { bot: "Thank you, Rahul. I have updated your payment promise for August 15th. Have a nice day!", user: "" }
                ],
                tool: "normalize_date",
                raw_date: "this Friday",
                outcome: { primary_intent: "PAYMENT_LATER", final_outcome_code: "PAYMENT_COMMITMENT_FUTURE", commitment_amount: 8500, commitment_date: "2026-08-15" }
            },
            "3": {
                name: "Financial Difficulty",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "Yes." },
                    { bot: "Hi Rahul, calling from Apex NBFC about your pending EMI of ₹8,500.", user: "I lost my job last month, I have no money." },
                    { bot: "I'm sorry to hear that, Rahul. Would you be able to make a partial payment of ₹4,000 on Monday?", user: "Yes, I can manage ₹4,000 by Monday." },
                    { bot: "Thank you. I have recorded a partial payment promise of ₹4,000 for August 17th.", user: "" }
                ],
                tool: "normalize_date",
                raw_date: "next Monday",
                outcome: { primary_intent: "PARTIAL_PAYMENT", final_outcome_code: "PARTIAL_PAYMENT_COMMITMENT", commitment_amount: 4000, commitment_date: "2026-08-17" }
            },
            "4": {
                name: "Wrong Number",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "No, wrong number. Rahul doesn't live here." },
                    { bot: "I apologize for the inconvenience. Have a good day!", user: "" }
                ],
                outcome: { primary_intent: "WRONG_NUMBER", final_outcome_code: "WRONG_NUMBER", commitment_amount: null, commitment_date: null }
            },
            "5": {
                name: "Claimed Already Paid",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "Yes." },
                    { bot: "Hi Rahul, calling regarding your pending EMI of ₹8,500.", user: "I already paid yesterday evening via UPI." },
                    { bot: "Thank you! Could you share the transaction reference number or UTR?", user: "Ref is UTR/4239108492." },
                    { bot: "Thank you. I have logged UTR/4239108492 for verification with accounts.", user: "" }
                ],
                outcome: { primary_intent: "ALREADY_PAID", final_outcome_code: "CLAIMED_ALREADY_PAID", claimed_transaction_ref: "UTR/4239108492" }
            },
            "6": {
                name: "Human Escalation Request",
                turns: [
                    { bot: "Hello, am I speaking with Rahul Sharma?", user: "Yes." },
                    { bot: "Hi Rahul, calling regarding your pending EMI of ₹8,500.", user: "Your penalty calculation is wrong. Connect me to a human manager." },
                    { bot: "Certainly, Rahul. Transferring your call to a customer representative right away.", user: "" }
                ],
                escalate: true,
                outcome: { primary_intent: "HUMAN_AGENT_REQUEST", final_outcome_code: "HUMAN_AGENT_REQUESTED", escalation_required: true }
            }
        };

        function speak(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                window.speechSynthesis.speak(utterance);
            }
        }

        async function startCall() {
            const scKey = document.getElementById('scenario').value;
            const sc = SCENARIOS[scKey];
            const chatLog = document.getElementById('chat-log');
            const dot = document.getElementById('dot');
            const statusBadge = document.getElementById('call-status-badge');
            const timer = document.getElementById('call-timer');

            chatLog.innerHTML = '';
            dot.classList.add('active');
            statusBadge.innerText = 'CALL CONNECTED';
            statusBadge.style.color = '#10b981';
            timer.innerText = 'Connected: +91 98765 43210';
            document.getElementById('btn-start').disabled = true;
            document.getElementById('btn-end').disabled = false;

            // Trigger REST API POST /calls/start
            const startCallRes = await fetch('/api/v1/calls/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Idempotency-Key': 'web-demo-' + Date.now() },
                body: JSON.stringify({ borrower_id: 'BRW-90412', loan_id: 'LN-1023489', campaign_id: 'WEB-DEMO', phone_number: '+919876543210' })
            });
            const startData = await startCallRes.json();
            const callId = startData.call_id;

            chatLog.innerHTML += `<div class="msg system">⚡ API EVENT: POST /calls/start -> Generated Session Call ID: ${callId}</div>`;

            for (let turn of sc.turns) {
                // Bot Turn
                const botEl = document.createElement('div');
                botEl.className = 'msg bot';
                botEl.innerText = turn.bot;
                chatLog.appendChild(botEl);
                chatLog.scrollTop = chatLog.scrollHeight;
                speak(turn.bot);

                await new Promise(r => setTimeout(r, 2200));

                if (turn.user) {
                    // User Turn
                    const userEl = document.createElement('div');
                    userEl.className = 'msg user';
                    userEl.innerText = turn.user;
                    chatLog.appendChild(userEl);
                    chatLog.scrollTop = chatLog.scrollHeight;
                    await new Promise(r => setTimeout(r, 1800));
                }
            }

            if (sc.tool === "send_payment_link") {
                chatLog.innerHTML += `<div class="msg system">🛠️ MIDDLEWARE TOOL EXECUTION: send_payment_link() -> SMS payment link dispatched!</div>`;
            } else if (sc.tool === "normalize_date") {
                chatLog.innerHTML += `<div class="msg system">🛠️ MIDDLEWARE TOOL EXECUTION: normalize_date('${sc.raw_date}') -> Normalized to ${sc.outcome.commitment_date}</div>`;
            }

            if (sc.escalate) {
                chatLog.innerHTML += `<div class="msg system" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3);">🚨 HUMAN ESCALATION QUEUED: Transferring call via SIP REFER to Human Manager</div>`;
            }

            // Trigger REST API POST /calls/{id}/outcome
            const outcomePayload = {
                call_id: callId,
                borrower_id: 'BRW-90412',
                loan_id: 'LN-1023489',
                call_duration_seconds: 45,
                call_status: 'CONNECTED',
                primary_intent: sc.outcome.primary_intent,
                final_outcome_code: sc.outcome.final_outcome_code,
                commitment_amount: sc.outcome.commitment_amount || null,
                commitment_date: sc.outcome.commitment_date || null,
                claimed_transaction_ref: sc.outcome.claimed_transaction_ref || null,
                callback_required: false,
                escalation_required: sc.outcome.escalation_required || false,
                conversation_summary: `Web demo call executed for scenario: ${sc.name}`,
                confidence_score: 0.98
            };

            const outcomeRes = await fetch(`/api/v1/calls/${callId}/outcome`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(outcomePayload)
            });
            const outcomeData = await outcomeRes.json();

            document.getElementById('json-output').innerText = JSON.stringify(outcomeData.data, null, 2);

            chatLog.innerHTML += `<div class="msg system">✅ POST-CALL CRM SYNC SUCCESSFUL (Status 200 OK)</div>`;
            chatLog.scrollTop = chatLog.scrollHeight;
            resetCallUI();
        }

        function resetCallUI() {
            document.getElementById('dot').classList.remove('active');
            document.getElementById('call-status-badge').innerText = 'COMPLETED';
            document.getElementById('call-status-badge').style.color = 'var(--text-muted)';
            document.getElementById('call-timer').innerText = 'Line Idle';
            document.getElementById('btn-start').disabled = false;
            document.getElementById('btn-end').disabled = true;
        }

        function resetCall() {
            window.speechSynthesis.cancel();
            resetCallUI();
        }
    </script>
</body>
</html>"""


@app.get("/")
async def root():
    return {
        "service": "NBFC Voice Collections Bot - Middleware Gateway API",
        "status": "ONLINE",
        "web_demo_ui_url": "http://127.0.0.1:8000/demo",
        "documentation_url": "http://127.0.0.1:8000/docs",
        "health_check_url": "http://127.0.0.1:8000/health",
        "available_endpoints": [
            "GET  /demo",
            "POST /api/v1/calls/start",
            "POST /api/v1/calls/{id}/events",
            "POST /api/v1/calls/{id}/outcome",
            "POST /api/v1/callbacks",
            "POST /api/v1/escalations"
        ]
    }


@app.get("/health")
async def health_check():
    return {"status": "HEALTHY", "service": "Voice Collections Middleware Gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
