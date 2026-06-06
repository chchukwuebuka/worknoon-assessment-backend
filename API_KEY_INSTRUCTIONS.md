# Adding an AI API Key

This project currently uses **Google Gemini** for its AI integration, but the architecture allows you to easily swap to another provider like **OpenAI** or **Anthropic**.

Here are the instructions on how to add and configure your AI API keys.

---

## 1. Using Google Gemini (Current Implementation)

By default, the project uses the `google-genai` SDK.

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a `.env` file in the root of the `backend` directory.
3. Add your key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
4. The application will automatically pick this up in `backend/support/services/ai_service.py`.

---

## 2. Switching to OpenAI (ChatGPT)

If you prefer to use OpenAI's models (like GPT-4), follow these steps:

1. Get an API key from the [OpenAI Developer Platform](https://platform.openai.com/).
2. Add your key to the `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```
3. Install the OpenAI Python package:
```bash
pip install openai
```
4. In `backend/support/services/ai_service.py`, replace the Gemini client initialization with OpenAI:
```python
import os
from openai import OpenAI

def get_ai_chat_response(customer_data, order_data, conversation_history):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Format system prompt and history for OpenAI
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content
```

---

## 3. Switching to Anthropic (Claude)

If you prefer to use Anthropic's models (like Claude 3.5 Sonnet), follow these steps:

1. Get an API key from the [Anthropic Console](https://console.anthropic.com/).
2. Add your key to the `.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
3. Install the Anthropic Python package:
```bash
pip install anthropic
```
4. In `backend/support/services/ai_service.py`, replace the Gemini client with Anthropic:
```python
import os
import anthropic

def get_ai_chat_response(customer_data, order_data, conversation_history):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Format history for Anthropic
    messages = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
        
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text
```
