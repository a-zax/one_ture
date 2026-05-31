# HDFC MF Generative AI Chatbot

This project implements the assignment brief:

- Use the HDFC Mutual Fund Factsheet - June 2024 as a vector-backed document knowledge base.
- Create a dummy customer database.
- Answer factsheet questions through retrieval augmented generation.
- Protect customer-specific answers with email verification and OTP-based 2FA.

## Tech Stack

- Streamlit for the chatbot UI
- pypdf for PDF extraction
- scikit-learn TF-IDF vectors as the local vector store
- SQLite seeded from CSV files for dummy customer data
- Optional Gemini or OpenAI integration for generated answers

The app works without an API key using an extractive fallback. Add a Gemini or OpenAI key for more natural final answers.

## Setup

```powershell
pip install -r requirements.txt
```

The app looks for the factsheet in either:

- `data/HDFC MF Factsheet -  June 2024.pdf`
- `C:\Users\Aryan Shukla.000\Downloads\HDFC MF Factsheet -  June 2024.pdf`

You can also set:

```powershell
$env:FACTSHEET_PATH="C:\Users\Aryan Shukla.000\Downloads\HDFC MF Factsheet -  June 2024.pdf"
```

Optional LLM key:

```powershell
$env:GOOGLE_API_KEY="your_key"
```

or

```powershell
$env:OPENAI_API_KEY="your_key"
```

## Run

```powershell
streamlit run app.py
```

## Demo Questions

Factsheet questions:

- What is the investment objective of HDFC Infrastructure Fund?
- Who manages HDFC Balanced Advantage Fund?
- What is the exit load mentioned in the factsheet?
- Explain SIP as per the factsheet.

Customer questions:

- What is my current portfolio value?
- What is my folio number?
- Show my holdings.
- What was my last transaction?

Sample registered emails:

- `aryan.shukla@example.com`
- `richa.tiwari@example.com`
- `omkar.dhavalikar@example.com`

## 2FA Flow

1. Ask a customer-specific question.
2. Enter a registered email in the sidebar.
3. Click **Send OTP**.
4. Read the generated OTP in the dummy email outbox.
5. Enter OTP and click **Verify OTP**.
6. The chatbot returns the customer-specific answer.

## Notes

This is a demo assignment project. OTP delivery is intentionally simulated through a dummy email outbox instead of a real email provider.
