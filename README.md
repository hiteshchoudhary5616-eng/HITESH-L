# Python Backend for AI Injury Prevention Assistant

This directory contains a complete Python implementation of the project's backend. It mirrors the exact database models, rule-based injury risk calculations, Gemini AI analysis, chatbot, and REST API endpoints found in the TypeScript version.

## Key Features

1. **Shared Database File (`db_storage.json`)**: Both the Node.js and Python backends share the same JSON database file. Changes made in one will immediately reflect in the other.
2. **Identical Risk Engine**: The rule-based scoring engine calculates factors, frequency warnings, overtraining, and difficulty mismatches exactly the same.
3. **Dual SDK Gemini Wrapper**: The AI service supports both the new `google-genai` and traditional `google-generativeai` SDKs with identical structured JSON schemas and local sports medicine rule-based fallback responses.
4. **FastAPI Web Server**: Built with FastAPI. You can run the Python backend on port `3000` as a drop-in replacement for the Node.js Express server.
5. **Diagnostics CLI Tool**: Run instant risk calculations and analysis on database records directly in the terminal without starting the web server.

---

## Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Install Dependencies
Run the following command in your terminal from the project root directory (or inside the `python_backend` folder):

```bash
pip install -r python_backend/requirements.txt
```

### 3. Set the Gemini API Key (Optional)
To use actual Gemini AI recommendations and chat responses, set your API key environment variable.

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-actual-api-key"
```

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-actual-api-key
```

**On Linux/macOS:**
```bash
export GEMINI_API_KEY="your-actual-api-key"
```

---

## How to Run

### Option A: Run the CLI Diagnostic Tool
This tool reads the active `db_storage.json` database, performs injury risk engine calculations, and runs the sports medicine AI analysis for the demo user:

```bash
python python_backend/cli.py
```

### Option B: Run the FastAPI Web Server (Drop-in Replacement)
To run the Python server as the backend for the React frontend, start FastAPI on port `3000`:

```bash
uvicorn python_backend.main:app --reload --port 3000
```

Once started, the React frontend running via Vite (`npm run dev`) will automatically send requests to this Python FastAPI server instead of the Express server.

---

## Project Structure Mapping

| Feature | TypeScript File | Python File |
| :--- | :--- | :--- |
| **JSON Database** | [server/db.ts](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/server/db.ts) | [python_backend/db.py](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/python_backend/db.py) |
| **Risk Calculation** | [server/risk_engine.ts](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/server/risk_engine.ts) | [python_backend/risk_engine.py](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/python_backend/risk_engine.py) |
| **Gemini AI Service** | [server/ai_service.ts](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/server/ai_service.ts) | [python_backend/ai_service.py](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/python_backend/ai_service.py) |
| **REST API Server** | [server.ts](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/server.ts) | [python_backend/main.py](file:///c:/AI%20PROJECT/ai-injury-prevention-assistant/python_backend/main.py) |
