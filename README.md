# HDFC MF Chatbot Assignment

This is a Streamlit chatbot built for the AIML assignment. The brief had two main parts:

- answer questions from the HDFC Mutual Fund Factsheet - June 2024
- answer customer-specific questions only after email and OTP verification

I kept these as two separate flows in the app because factsheet data is public document data, while customer data should be protected.

## What The App Does

For factsheet questions, the app reads the PDF from the `data` folder, extracts the text, breaks it into chunks, and searches those chunks using a local TF-IDF based retrieval index. The retrieved context is then passed to Gemini so the final answer is generated from the factsheet content. The response also shows source page numbers.

For customer questions, the app first checks whether the user is authenticated. If not, it asks for a registered email in the sidebar, generates a dummy OTP, and verifies the OTP before showing customer details. The customer data is dummy data stored in CSV files and loaded into SQLite.

## Main Files

- `app.py` - Streamlit UI and chat flow
- `src/document_rag.py` - PDF extraction, chunking, and factsheet retrieval
- `src/llm.py` - Gemini/OpenAI answer generation with a local fallback
- `src/customer_db.py` - dummy customer database lookup and response formatting
- `src/auth.py` - OTP generation and validation
- `src/router.py` - decides whether a query is for the factsheet or customer database
- `data/customers.csv` - dummy customer records
- `data/holdings.csv` - dummy customer holdings
- `data/HDFC MF Factsheet -  June 2024.pdf` - factsheet used for document Q&A

## Tech Used

- Python
- Streamlit
- pypdf
- scikit-learn TF-IDF
- SQLite
- Google Gemini 2.5 Flash
- python-dotenv

The app can still run without an LLM key, but the factsheet answers are better when `GOOGLE_API_KEY` is configured.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-2.5-flash
```

Do not commit `.env`. It is already ignored in `.gitignore`.

## Run

```powershell
streamlit run app.py
```

The app should open at:

```text
http://localhost:8501
```

## Demo Questions

Factsheet:

- What is the investment objective of HDFC Infrastructure Fund?
- What is the benchmark of HDFC Infrastructure Fund?
- Who manages HDFC Balanced Advantage Fund?
- Explain SIP as per the factsheet.
- What is NAV?

Customer:

- What is my current portfolio value?
- What is my folio number?
- Show my holdings.
- What is my SIP amount?
- What was my last transaction?

Sample registered emails:

- `aryan.shukla@example.com`
- `richa.tiwari@example.com`
- `omkar.dhavalikar@example.com`

## 2FA Demo Flow

1. Ask a customer question, for example: `What is my current portfolio value?`
2. Enter a registered email in the sidebar.
3. Click `Send OTP`.
4. Copy the OTP from the dummy email outbox.
5. Enter the OTP and click `Verify OTP`.
6. Ask the customer question again, or continue with another customer query.
