# Worknoon Assessment - Backend

This is the backend repository for the **AI-Powered Support Assistant** built as part of the Full Stack Engineer assessment for Worknoon. It provides a RESTful API powered by Django REST Framework and integrates with the Google Gemini AI API to provide intelligent, policy-driven customer support.

## 🌟 Overview

The backend is responsible for:
1. Managing the SQLite database (Customers, Orders, Conversations, and Messages).
2. Supplying endpoints to create and retrieve chat histories.
3. Acting as the secure intermediary that interacts with the **Google Gemini AI**.
4. Enforcing strict business logic via a custom system prompt that tells the AI exactly how to approve, deny, or escalate a request based on the company refund policy.

## 🛠️ Tech Stack
- **Python 3**
- **Django 6** & **Django REST Framework (DRF)**
- **Google GenAI SDK** (Gemini 2.5 Flash)
- **django-cors-headers** (to communicate with the React frontend)

## 🚀 How to Run the Project Locally

### 1. Prerequisites
- Python 3.10+ installed
- Virtual environment tool (`venv`)

### 2. Setup the Environment
Clone this repository and navigate into the backend folder:
```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.\.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Add Your AI API Key
The AI logic relies on the Gemini API. You need to provide your API key.
1. Create a file named `.env` in the root of the backend directory.
2. Add your Gemini API key to the `.env` file like this:
```env
GEMINI_API_KEY=your_actual_api_key_here
```
*(If you do not have an API key, you can get one from Google AI Studio).*

### 4. Setup the Database
Run the migrations to create the SQLite database tables and seed it with test data:
```bash
# Apply database migrations
python manage.py migrate

# Seed the database with 8 distinct test customer scenarios
python manage.py seed_data
```

### 5. Start the Server
```bash
python manage.py runserver
```
The API will now be running on `http://localhost:8000/`.

---

## 🧠 How the AI Integration Works

The frontend communicates with the backend via REST APIs. When a customer sends a message:
1. The backend (`views.py`) intercepts the request and retrieves the customer profile, their recent order history, and the full chat history.
2. It bundles all this data, alongside a **Strict System Prompt** containing the company's refund policies (e.g., 14-day rules, final sale rules), and sends it to the **Gemini AI API** (`services/ai_service.py`).
3. The AI processes the request using multi-turn reasoning, evaluates the refund policy, and generates a conversational response acting as "Alex" the support agent.
4. The response is saved to the database and sent back to the React frontend.

## 🔗 Links
- **Frontend Repository**: [GitHub Link to Frontend Repo]
- **Video Walkthrough**: *(Video link goes here)*
