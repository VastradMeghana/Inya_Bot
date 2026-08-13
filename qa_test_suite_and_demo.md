# Voice Collections Agent - Comprehensive QA Test Suite (20 Scenarios) & Demo Scripts

Systematic QA test matrix covering 20 edge-case and production scenarios alongside 6 end-to-end demonstration scripts.

---

## 1. COMPREHENSIVE QA TEST SUITE (20 SCENARIOS)

| Test ID | Scenario Name | Input Utterance | Expected Intent | Bot Strategy | Expected Next State | Expected Outcome Code | Pass Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Pay Immediately | "I can pay right now via UPI" | `PAYMENT_READY` | Offer SMS UPI payment link | `CONFIRM_PAYMENT_DETAILS` | `PAYMENT_COMMITMENT_TODAY` | Payment SMS tool invoked, outcome logged within 2s. |
| `TC-02` | Pay Later (Relative Date) | "I will pay this Friday" | `PAYMENT_LATER` | Invoke `normalize_date()`, confirm exact date | `PROMPT_SPECIFIC_DATE` | `PAYMENT_COMMITMENT_FUTURE` | Raw date "this Friday" converted to `2026-08-15` & confirmed. |
| `TC-03` | Partial Payment Offer | "I can only pay ₹4,000 today" | `PARTIAL_PAYMENT` | Validate >= 50% threshold, capture date for remainder | `EXPLORE_PARTIAL_PAYMENT` | `PARTIAL_PAYMENT_COMMITMENT` | Partial amount ₹4,000 accepted and remaining balance flagged. |
| `TC-04` | Financial Hardship | "I lost my job last month" | `FINANCIAL_DIFFICULTY` | Empathy ack, check partial capability, escalate | `TRANSFER_HUMAN` | `FINANCIAL_HARDSHIP` | Human escalation ticket queued with priority HIGH. |
| `TC-05` | Wrong Number | "Wrong number, Rahul moved out" | `WRONG_NUMBER` | Zero loan info disclosed, polite exit | `STOP_LOAN_DISCLOSURE` | `WRONG_NUMBER` | Call terminated immediately, no loan EMI disclosed. |
| `TC-06` | Already Paid Claim | "I paid yesterday via GPay" | `ALREADY_PAID` | Request transaction reference / UTR | `CAPTURE_PAYMENT_DETAILS` | `CLAIMED_ALREADY_PAID` | UTR reference captured and sent for reconciliation. |
| `TC-07` | Callback Request | "I am driving, call after 5 PM" | `CALLBACK_REQUEST` | Normalize time, confirm callback slot | `CAPTURE_CALLBACK_SLOT` | `CALLBACK_SCHEDULED` | CRM dialer updated with callback timestamp `17:00`. |
| `TC-08` | Human Escalation Req | "Connect me to a real agent" | `HUMAN_AGENT_REQUEST` | Immediate compliance, initiate transfer | `TRANSFER_HUMAN` | `HUMAN_AGENT_REQUESTED` | SIP REFER triggered without argumemt/delay. |
| `TC-09` | Do Not Call (DNC) | "Put me on DNC list, stop calling"| `DO_NOT_CALL` | Record compliance preference, exit | `LOG_DNC_PREFERENCE` | `DNC_REQUESTED` | DNC status set to `true` in LMS DB. |
| `TC-10` | Third Party Answered | "I am his brother, he is out" | `THIRD_PARTY_ANSWERED` | Privacy check, request callback info | `HANDLE_THIRD_PARTY` | `THIRD_PARTY_CONTACT` | Zero loan details disclosed to family member. |
| `TC-11` | Borrower Denies Loan | "I never took any loan from you"| `BORROWER_DENIES_LOAN` | Flag dispute, escalate to legal/ops | `LOG_DISPUTE` | `LOAN_DISOWNED_DISPUTE` | Account flagged for fraud/identity investigation. |
| `TC-12` | Explicit Refusal | "I won't pay, do whatever" | `REFUSES_TO_PAY` | Calm acknowledgment, escalate | `TRANSFER_HUMAN` | `REFUSED_TO_PAY` | Escalate to recovery manager without arguing. |
| `TC-13` | Fee / Interest Dispute | "Penalty was added unfairly" | `DISPUTE` | Capture dispute details, escalate | `LOG_DISPUTE` | `ACCOUNT_DISPUTE_ESCALATED` | Dispute ticket logged in CRM with notes. |
| `TC-14` | Mid-call Language Switch| "Hindi me baat kar sakte ho?" | `LANGUAGE_CHANGE` | Switch TTS/ASR model to Hindi prompt | `SWITCH_LANGUAGE_STATE` | `LANGUAGE_SWITCHED` | Context retained, response rendered in natural Hindi. |
| `TC-15` | Borrower Silence (Strike 3)| *Silence for 10 seconds* | `SILENCE` | 3-strike prompt recovery | `FALLBACK_RECOVERY` | `NO_CONTACT_SILENCE` | Bot prompts at 3s and 6s, disconnects at 10s. |
| `TC-16` | Noisy Background | *Muffled audio / noise* | `UNCLEAR_RESPONSE` | Ask binary yes/no question, then escalate | `FALLBACK_RECOVERY` | `UNCLEAR_AUDIO_ESCALATED` | Escalated to human queue after 2 failed turns. |
| `TC-17` | Interruption / Barge-in | *Borrower speaks mid-prompt* | `PAYMENT_READY` | Stop TTS immediately, process audio | `CONFIRM_PAYMENT_DETAILS` | `PAYMENT_COMMITMENT_TODAY` | Bot TTS halts within <200ms of user speech. |
| `TC-18` | Vague Date | "I'll pay sometime next week" | `PAYMENT_LATER` | Re-prompt for specific day | `PROMPT_SPECIFIC_DATE` | `PAYMENT_COMMITMENT_FUTURE` | Bot asks: "Could you specify the exact day?" |
| `TC-19` | Invalid Date Offer | "I'll pay on February 31st" | `PAYMENT_LATER` | Middleware validates & prompts re-entry | `PROMPT_SPECIFIC_DATE` | `PAYMENT_COMMITMENT_FUTURE` | Invalid date rejected by middleware, bot asks valid date. |
| `TC-20` | Middleware API Timeout | *API returns 504 Gateway Timeout*| `SYSTEM_ERROR` | Fallback to offline queue logging | `GRACEFUL_DISCONNECT` | `SYSTEM_ERROR_ESCALATED` | Call exits gracefully: "We'll call back shortly". |

---

## 2. SIX REPRESENTATIVE DEMO CALL SCRIPTS

```carousel
### DEMO 1: Successful Payment Commitment (UPI SMS)
**Scenario**: Rahul Sharma agrees to pay overdue EMI immediately.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "Yes, Rahul speaking."
- **Agent**: "Hi Rahul, calling from Apex NBFC. Your EMI of ₹8,500 was due on August 10th. May I know when you will pay?"
- **Borrower**: "I can pay right now if you send the link."
- **Agent**: "Thank you! I am sending an instant UPI payment link to your mobile number via SMS now."
- **Outcome**: `PAYMENT_COMMITMENT_TODAY` | Payment SMS Triggered

<!-- slide -->

### DEMO 2: Payment Later (Relative Date Normalization)
**Scenario**: Borrower commits to pay on Friday after salary.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "Yes."
- **Agent**: "Hi Rahul, calling from Apex NBFC regarding your pending EMI of ₹8,500 due on August 10th."
- **Borrower**: "I get my salary this Friday, I'll pay then."
- **Agent**: "Got it. So you're committing to pay ₹8,500 on Friday, August 15th, correct?"
- **Borrower**: "Yes, correct."
- **Outcome**: `PAYMENT_COMMITMENT_FUTURE` | Date: `2026-08-15`

<!-- slide -->

### DEMO 3: Financial Difficulty (Empathy & Partial Payment)
**Scenario**: Borrower lost job, agrees to minimum partial payment.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "Yes."
- **Agent**: "Hi Rahul, calling from Apex NBFC regarding your overdue EMI of ₹8,500."
- **Borrower**: "I lost my job last month, I have no money."
- **Agent**: "I'm sorry to hear that, Rahul. Would you be able to make a partial payment of ₹4,000 on Monday to keep your account active?"
- **Borrower**: "Yes, I can manage ₹4,000 by Monday."
- **Outcome**: `PARTIAL_PAYMENT_COMMITMENT` | Amount: `4000` | Date: `2026-08-18`

<!-- slide -->

### DEMO 4: Wrong Number (Zero Privacy Leakage)
**Scenario**: Recipient is not the borrower.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "No, wrong number. Rahul doesn't live here."
- **Agent**: "I apologize for the inconvenience. Have a good day!"
- **Outcome**: `WRONG_NUMBER` | Zero loan details disclosed

<!-- slide -->

### DEMO 5: Claimed Already Paid (UTR Capture)
**Scenario**: Borrower claims payment done yesterday via UPI.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "Yes, tell me."
- **Agent**: "Hi Rahul, calling regarding your pending EMI of ₹8,500 due on August 10th."
- **Borrower**: "I already paid yesterday evening via UPI."
- **Agent**: "Thank you! Could you share the transaction reference number or UTR?"
- **Borrower**: "Ref is 4239108492."
- **Outcome**: `CLAIMED_ALREADY_PAID` | UTR: `4239108492`

<!-- slide -->

### DEMO 6: Human Escalation Request
**Scenario**: Borrower demands human representative for fee dispute.
- **Agent**: "Hello, am I speaking with Rahul Sharma?"
- **Borrower**: "Yes."
- **Agent**: "Hi Rahul, calling from Apex NBFC about your pending EMI of ₹8,500."
- **Borrower**: "Your penalty calculation is completely wrong. Connect me to a human manager."
- **Agent**: "Certainly, Rahul. Transferring your call to a customer representative right away."
- **Outcome**: `HUMAN_AGENT_REQUESTED` | SIP Transfer Initiated
```
