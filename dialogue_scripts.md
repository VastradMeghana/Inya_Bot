# Voice Collections Agent - Natural Phone Dialogue Scripts

Realistic, short, phone-optimized dialogues for early-stage collections (1–30 DPD) designed for audio playback on Inya.

---

## Script 1: Happy Path - Immediate Payment Commitment (UPI Link)

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "Yes, Rahul speaking."  
**Agent**: "Hi Rahul, I'm calling from Apex NBFC regarding your loan account. Is now a good time to speak for a minute?"  
**Borrower**: "Yes, tell me."  
**Agent**: "Your EMI of ₹8,500 was due on August 10th and is currently pending. May I know when you will make the payment?"  
**Borrower**: "Oh, I forgot. Can I pay it right now?"  
**Agent**: "Thank you! I am sending an instant UPI payment link to your mobile number via SMS. Will you complete it today?"  
**Borrower**: "Yes, I will pay it as soon as I get the SMS."  
**Agent**: "Great! I've sent the link. Once paid, your account status will update automatically. Have a great day!"  
*(Call Outcome: `PAYMENT_COMMITMENT_TODAY` | Payment SMS triggered)*

---

## Script 2: Payment Later - Date Negotiation & Confirmation

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "Yeah, who is this?"  
**Agent**: "Hi Rahul, I'm calling from Apex NBFC regarding your overdue loan EMI. Is now a good time?"  
**Borrower**: "Yeah, go ahead."  
**Agent**: "Your EMI of ₹8,500 was due on August 10th. May I know when you expect to make the payment?"  
**Borrower**: "I don't have funds today. I'll pay later."  
**Agent**: "I understand. Could you please share the exact date by which you will make the payment?"  
**Borrower**: "I'll get my salary this Friday, so August 15th."  
**Agent**: "Got it. So you're committing to pay the full ₹8,500 on Friday, August 15th, correct?"  
**Borrower**: "Yes, correct."  
**Agent**: "Thank you, Rahul. I have updated your payment promise for August 15th. Have a nice day!"  
*(Call Outcome: `PAYMENT_COMMITMENT_FUTURE` | Date: `2026-08-15`)*

---

## Script 3: Financial Difficulty - Empathy & Partial Payment Negotiation

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "Yes."  
**Agent**: "Hi Rahul, calling from Apex NBFC about your pending EMI of ₹8,500 due on August 10th. Can we discuss payment today?"  
**Borrower**: "Listen, I am facing severe financial difficulty right now. I lost my job last month."  
**Agent**: "I'm really sorry to hear that, Rahul. I understand this is a tough situation. Would you be able to make a partial payment of ₹4,250 today to keep your account in good standing?"  
**Borrower**: "I can manage ₹4,000 by Monday, but not more than that right now."  
**Agent**: "Thank you for working with us, Rahul. I will record a partial payment promise of ₹4,000 for Monday, August 18th, and note the remaining balance for review. Does that work?"  
**Borrower**: "Yes, that works. Thanks."  
**Agent**: "You're welcome. I've updated your record. Take care!"  
*(Call Outcome: `PARTIAL_PAYMENT_COMMITMENT` | Amount: `4000` | Date: `2026-08-18`)*

---

## Script 4: Wrong Number Protection (Privacy First)

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "No, Rahul doesn't use this number. This is Vikram."  
**Agent**: "I apologize for the inconvenience, Vikram. Have a great day!"  
*(Call Outcome: `WRONG_NUMBER` | Zero loan details disclosed)*

---

## Script 5: Claimed Already Paid - Reference Capture

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "Yes, speaking."  
**Agent**: "Hi Rahul, calling from Apex NBFC regarding your pending EMI of ₹8,500 due on August 10th."  
**Borrower**: "Hey, I already paid this yesterday evening through Google Pay!"  
**Agent**: "Thank you for letting us know! Could you share the transaction reference number or UTR if you have it handy?"  
**Borrower**: "Yeah, UTR is 4239108492."  
**Agent**: "Got it, 4239108492. I've submitted this to our reconciliation team for verification. Thank you, Rahul!"  
*(Call Outcome: `CLAIMED_ALREADY_PAID` | UTR captured)*

---

## Script 6: Human Escalation Request

**Agent**: "Hello, am I speaking with Rahul Sharma?"  
**Borrower**: "Yes, tell me."  
**Agent**: "Hi Rahul, calling from Apex NBFC regarding your pending EMI of ₹8,500."  
**Borrower**: "I want to dispute the penalty charges added to my account. Connect me to a human agent right now."  
**Agent**: "Certainly, Rahul. I am transferring your call to a senior customer support representative right away. Please stay on the line."  
*(Call Outcome: `HUMAN_AGENT_REQUESTED` | SIP Transfer initiated)*
