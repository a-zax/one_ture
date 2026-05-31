# HDFC MF Generative AI Chatbot

This project implements a document-aware financial chatbot with two protected data paths:

- answer questions from the HDFC Mutual Fund Factsheet - June 2024
- answer customer-specific questions only after email and OTP verification

The system keeps these as separate flows because factsheet data is public document data, while customer data needs an authentication boundary.

## What The App Does

For factsheet questions, the app reads the PDF from the `data` folder, extracts the text, breaks it into chunks, and searches those chunks using a local TF-IDF based retrieval index. The retrieved context is then passed to the configured LLM provider so the final answer is generated from the factsheet content. The response also shows source page numbers.

For customer questions, the app first checks whether the user is authenticated. If not, it asks for a registered email in the sidebar, generates an OTP in a simulated email outbox, and verifies the OTP before showing customer details. The customer records are sample records stored in CSV files and loaded into SQLite.

## Main Files

- `app.py` - Streamlit UI and chat flow
- `src/document_rag.py` - PDF extraction, chunking, and factsheet retrieval
- `src/llm.py` - Colab/Gemini/OpenAI answer generation with retrieval fallback
- `src/customer_db.py` - customer database lookup and response formatting
- `src/auth.py` - OTP generation and validation
- `src/router.py` - decides whether a query is for the factsheet or customer database
- `data/customers.csv` - sample customer records
- `data/holdings.csv` - sample customer holdings
- `data/HDFC MF Factsheet -  June 2024.pdf` - factsheet used for document Q&A

## Tech Used

- Python
- Streamlit
- pypdf
- scikit-learn TF-IDF
- SQLite
- Google Gemini 2.5 Flash
- optional Colab T4 open-source LLM endpoint
- python-dotenv

The app can use Gemini, OpenAI, or a temporary Colab T4 endpoint running an open-source model. If no provider is available, it still returns locally retrieved factsheet snippets.

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

Optional Colab T4 endpoint:

```env
COLAB_LLM_URL=https://your-url.trycloudflare.com
COLAB_LLM_TIMEOUT=90
```

Do not commit `.env`. It is already ignored in `.gitignore`.

## Optional Colab LLM

The repo includes a Colab notebook for running an open-source model on T4 GPU:

```text
docs/Colab_T4_Open_Source_LLM.ipynb
```

Provider order:

1. Colab open-source LLM, if `COLAB_LLM_URL` is set
2. Gemini, if `GOOGLE_API_KEY` is set
3. OpenAI, if `OPENAI_API_KEY` is set
4. local retrieval fallback

## Run

```powershell
streamlit run app.py
```

The app should open at:

```text
http://localhost:8501
```

## Example Queries

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

## 2FA Flow

1. Ask a customer question, for example: `What is my current portfolio value?`
2. Enter a registered email in the sidebar.
3. Click `Send OTP`.
4. Copy the OTP from the simulated email outbox.
5. Enter the OTP and click `Verify OTP`.
6. Ask the customer question again, or continue with another customer query.
