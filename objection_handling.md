# Voice Collections Agent - Objection Handling & Escalation Matrix

Enterprise objection handling strategy enforcing compliance, empathy, and deterministic outcome capture.

---

## 1. "I'll Pay Later" / Vague Promises
- **Borrower Objection**: "I'll pay later", "Call me next week", "I'll clear it soon".
- **Bot Response Strategy**: Acknowledge without accepting vagueness. Prompt for a firm calendar date.
- **Bot Script**: "I understand. Could you please specify the exact date by which you will make the payment?"
- **Normalization Rule**: Pass borrower utterance ("next Monday", "by 15th") to `normalize_date()` middleware.
- **Confirmation Requirement**: Bot must repeat confirmed date and amount back to borrower before logging.

---

## 2. Severe Financial Hardship / Job Loss
- **Borrower Objection**: "I lost my job", "Medical emergency in family", "No money at all".
- **Bot Response Strategy**: 
  1. Show genuine empathy without being overly verbose.
  2. Offer minimum threshold partial payment (e.g. 50% EMI).
  3. If partial payment is impossible, escalate immediately to human hardship resolution desk.
- **Bot Script (Step 1)**: "I'm sorry to hear that. I understand things are difficult right now. Would you be able to make a partial payment of ₹{{borrower.min_partial_amount}} today?"
- **Bot Script (Step 2 - Hardship Escalation)**: "I see. Let me transfer you to a specialist who can help explore alternative payment options." -> `escalate_human(reason="HARDSHIP")`.

---

## 3. Wrong Number / Third Party Answering
- **Borrower Objection**: "Wrong number", "Rahul doesn't live here", "I am his colleague".
- **Compliance Constraint**: **DO NOT DISCLOSE LOAN DETAILS OR EMI AMOUNTS**.
- **Bot Strategy**: 
  - If Wrong Number: Apologize, end call immediately, mark `WRONG_NUMBER` in CRM.
  - If Third Party: Ask third party to convey callback request without mentioning debt/collections.

---

## 4. Claimed Already Paid
- **Borrower Objection**: "I already paid yesterday", "Amount was deducted".
- **Bot Strategy**: Never argue or question borrower's integrity. Request transaction reference / UTR for verification.
- **Bot Script**: "Thank you for informing us. Could you share the transaction reference number or payment mode so our accounting team can verify and clear your account?"
- **Outcome Code**: `CLAIMED_ALREADY_PAID` with captured UTR metadata.

---

## 5. Explicit Refusal to Pay / Angry Borrower
- **Borrower Objection**: "I will not pay", "Do whatever you want", "Stop calling me!"
- **Bot Strategy**: Maintain absolute composure. Never raise voice, threaten legal action, or argue.
- **Bot Script**: "I understand your stance. I am logging your response and transferring your file to our senior resolution team for further assistance."
- **Outcome Code**: `REFUSED_TO_PAY` -> Escalate to human recovery manager.

---

## 6. Language Switch Request
- **Borrower Request**: "Hindi me baat me karo", "Kannada mathadi", "Speak in Tamil".
- **Bot Strategy**: Detect requested language, confirm switch, transition seamlessly while retaining state.
- **Bot Script (Hindi)**: "Namaste Rahul. Apex NBFC se baat kar rahe hain. Kya aap Hindi me baat karna chahenge?"

---

## 7. Request for Human Agent / Dispute / Fraud
- **Borrower Request**: "I want to talk to a human", "This loan is fraudulent", "Interest calculation is wrong".
- **Bot Strategy**: Respect request instantly without resistance.
- **Bot Script**: "Understood. Transferring your call to a customer representative now. Please stay connected." -> `escalate_human(reason="USER_REQUEST")`.
