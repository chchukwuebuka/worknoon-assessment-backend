import os
import json
from google import genai
from pydantic import BaseModel
from django.conf import settings
from support.policies import SUPPORT_POLICY


class AIResponse(BaseModel):
    decision: str
    reason: str


def get_ai_support_response(customer_data, order_data, message):
    """Original single-shot AI response (kept for backward compatibility)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {"decision": "ESCALATED", "reason": "System error: No AI API key provided. Escalating to human agent."}

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are a customer support assistant.

Support Policy:
{SUPPORT_POLICY}

Customer Information:
{customer_data}

Order Information:
{order_data}

Customer Request:
{message}

Determine based ONLY on the support policy above whether the request should be:
1. APPROVED
2. DENIED
3. ESCALATED

Provide a short explanation.

Return ONLY a valid JSON object in the following format:
{{
  "decision": "APPROVED/DENIED/ESCALATED",
  "reason": "explanation here"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # Strip potential markdown code blocks like ```json ... ```
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        return {
            "decision": result.get("decision", "ESCALATED"),
            "reason": result.get("reason", "Could not parse reason.")
        }
    except Exception as e:
        print(f"Error calling AI API: {e}")
        return {"decision": "ESCALATED", "reason": "Failed to evaluate via AI. Escalating."}


def get_ai_chat_response(customer_data, order_data, conversation_history):
    """
    Conversational AI response that takes the full chat history into account.
    
    Args:
        customer_data: String with customer info.
        order_data: String with order info.
        conversation_history: List of dicts with 'role' and 'content' keys.
    
    Returns:
        A string with the AI's reply.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "I'm sorry, I'm unable to process your request right now due to a system configuration issue. Please try again later or contact a human agent."

    client = genai.Client(api_key=api_key)

    # Build the conversation history string
    history_text = ""
    for msg in conversation_history:
        role_label = "Customer" if msg["role"] == "user" else "Support Agent (You)"
        history_text += f"{role_label}: {msg['content']}\n"

    import datetime
    today = datetime.datetime.now().date()
    
    system_prompt = f"""You are Alex, a friendly, professional AI customer support agent for Worknoon. You help customers with product inquiries, refund requests, order issues, and general questions.

TODAY's DATE: {today}

COMPANY SUPPORT POLICY (you MUST follow these rules strictly):
{SUPPORT_POLICY}

CUSTOMER INFORMATION:
{customer_data}

ORDER INFORMATION:
{order_data}

HOW TO APPLY THE POLICY — follow this decision flow for refund/return requests strictly in this order:

1. FIRST, check the purchase date against today's date.
   - If the purchase was MORE than 14 days ago → DENY the refund immediately. Explain: "Our return window is strictly 14 days from the date of purchase. Unfortunately, your purchase is outside this window, so we cannot process a refund, even for damaged items."

2. SECOND, check if the item is marked "Final Sale: True" in the ORDER INFORMATION.
   - If Final Sale = True → DENY the refund immediately. Explain: "Per our company policy, items purchased as final sale are not eligible for refunds or returns."

3. THIRD, check the product condition and amount.
   - If the customer claims the product is damaged or incorrect, or they just want a standard return:
     - Check the order amount.
     - If the amount is $500 or less → APPROVE the refund. Explain: "Your refund request is approved. I am forwarding this to our Billing Team to process the transaction. You will see the funds returned to your original payment method within 3-5 business days."
     - If the amount is over $500 → ESCALATE. Explain you are transferring them to our **Senior Refunds Team** who handles high-value claims.

ESCALATION DETAILS (use when escalating):
- Team: "Senior Refunds Team"
- What happens: The customer's case file and conversation history will be forwarded to the Senior Refunds Team for manual review.
- Timeline: 1-2 business days for a decision.
- Reference: A case reference number will be assigned.

CONVERSATION RULES:
- IMPORTANT: In your VERY FIRST response to the customer, you MUST say "Welcome to Worknoon!" and introduce yourself as Alex.
- Always cite the specific policy rule when making a decision (e.g., "Per our 14-day return policy..." or "Since this item was marked as final sale...").
- Be conversational, warm, and empathetic — not robotic.
- If the customer asks follow-up questions about the policy, explain clearly.
- If the customer disagrees with a denial, acknowledge their frustration, but hold firm on the policy. You may suggest they contact our Customer Relations team at support@worknoon.com for further review.
- If the customer asks about something unrelated to their order, gently redirect them.
- Keep responses concise (2-4 sentences) unless the customer asks for more detail.
- Do NOT output JSON. Respond in natural, conversational language.
- Address the customer by their first name.
"""

    try:
        # Build the Gemini contents list for multi-turn
        contents = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config={
                "system_instruction": system_prompt,
            }
        )

        return response.text.strip()

    except Exception as e:
        print(f"Error calling AI Chat API: {e}")
        return "I apologize, but I'm experiencing a technical issue right now. Please try again in a moment, or if the issue persists, I can escalate your request to a human agent."
