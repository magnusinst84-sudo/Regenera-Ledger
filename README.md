# Regenera Ledger: AI-Powered ESG Intelligence & Carbon Transparency

An end-to-end platform for automated ESG forensic auditing, Scope 3 supply chain reasoning, and Company-to-Farmer carbon credit matching. Powered by Google Gemini 2.0 and Firebase.

## 🌟 Key Features

*   **Forensic ESG Auditor**: Upload ESG reports (PDF) to detect greenwashing, verify reported emissions vs. detected risk, and uncover "red flags."
*   **Scope 3 Whistleblower**: Cross-reference shipping manifests with corporate reports to identify undisclosed supply chain emissions.
*   **Carbon Gap Analysis**: Real-time calculation of the "Carbon Gap" between corporate claims and data-driven estimates.
*   **Regenerative Farmer Marketplace**: Match carbon-heavy companies with verified regenerative farmers for direct carbon sequestration projects.
*   **AI Farmer Estimation**: Leverages Gemini to estimate sequestration capacity based on soil, crop, and location data.
*   **Full Audit Logging**: Every sensitive action is logged for compliance and forensic accountability.

## 🏗 Tech Stack

*   **Frontend**: React (Vite), Chart.js, Leaflet (Maps), Axios.
*   **Backend**: Python (FastAPI), Pydantic.
*   **Intelligence Engine**: Google Gemini 2.0 (via `google-genai`).
*   **Data Processing**: PDFMiner, Pandas, Custom T2 Bridge modules.
*   **Database & Auth**: Firebase Firestore + JWT (PyJWT).

## 📁 Project Structure

```
GEMINATHON/
├── backend/            # FastAPI Backend
│   ├── ai/             # Gemini API Client
│   ├── data/           # PDF/Manifest parsers & processing logic
│   ├── middleware/     # Auth & Error handlers
│   ├── prompts/        # Gemini prompt engineering templates
│   ├── routes/         # API Endpoints (ESG, Farmer, Matching, etc.)
│   └── utils/          # File upload & Audit logging
├── frontend/           # React Frontend (Vite)
├── database/           # Firestore schema & security rules
└── README.md           # You are here!
```

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Google Gemini API Key ([AI Studio](https://aistudio.google.com/))
*   Firebase Service Account Key ([Firebase Console](https://console.firebase.google.com/))

### 2. Backend Setup
1.  Navigate to the backend folder:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Place your `firebase-service-account.json` in the `backend/` directory.
4.  Create a `.env` file (refer to `.env.example`) and add your keys:
    ```env
    GEMINI_API_KEY=your_key_here
    JWT_SECRET=some_random_secret
    ```
5.  Seed the database with demo data:
    ```bash
    python seed.py
    ```
6.  Start the server:
    ```bash
    uvicorn main:app --reload
    ```

### 3. Frontend Setup
1.  Navigate to the frontend folder:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the dev server:
    ```bash
    npm run dev
    ```

## 🔐 Security Disclaimer
For high-security production environments, ensure you replace the `JWT_SECRET` and follow best practices for Cloud Firestore security rules (provided in `database/firestore.rules`).

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
