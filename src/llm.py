from __future__ import annotations

import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def generate_document_answer(query: str, context: str) -> str:
    provider_answer = _try_google(query, context) or _try_openai(query, context)
    if provider_answer:
        return provider_answer

    return _fallback_answer(context)


def _try_google(query: str, context: str) -> str | None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    model_name = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL)

    answer = _try_google_genai_sdk(api_key, model_name, query, context)
    if answer:
        return answer

    return _try_legacy_google_sdk(api_key, model_name, query, context)


def _try_google_genai_sdk(api_key: str, model_name: str, query: str, context: str) -> str | None:
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=_prompt(query, context),
        )
        return response.text.strip() if response.text else None
    except ImportError:
        return None
    except Exception:
        return _provider_fallback("Gemini is configured but the request failed. Check GOOGLE_API_KEY and GOOGLE_MODEL.")


def _try_legacy_google_sdk(api_key: str, model_name: str, query: str, context: str) -> str | None:
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(_prompt(query, context))
        return response.text.strip()
    except ImportError:
        return None
    except Exception:
        return _provider_fallback("Gemini is configured but the request failed. Check GOOGLE_API_KEY and GOOGLE_MODEL.")


def _try_openai(query: str, context: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Answer strictly from the supplied factsheet context. If the answer is not present, say so."},
                {"role": "user", "content": _prompt(query, context)},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _provider_fallback("OpenAI is configured but the request failed. Check OPENAI_API_KEY and OPENAI_MODEL.")


def _prompt(query: str, context: str) -> str:
    return f"""
You are a mutual fund factsheet assistant.
Use only the provided context from the HDFC Mutual Fund Factsheet - June 2024.
Do not provide investment advice.
If the context does not contain the answer, say the factsheet context does not contain enough information.

Question:
{query}

Factsheet context:
{context}

Answer in a concise, user-friendly way and mention relevant page numbers if present in the context.
""".strip()


def _fallback_answer(context: str) -> str:
    snippets = [block.strip() for block in context.split("\n\n") if block.strip()]
    if not snippets:
        return "I could not find relevant factsheet content for that question."

    compact = []
    for snippet in snippets[:3]:
        snippet = re.sub(r"\s+", " ", snippet)
        compact.append(snippet)

    return (
        "I found the following relevant factsheet content. Add a Gemini or OpenAI API key for a more polished generated answer.\n\n"
        + "\n\n".join(compact)
        + "\n\nNote: Mutual fund investments are subject to market risks. This is not investment advice."
    )


def _provider_fallback(message: str) -> str:
    return f"{message}\n\nThe app is falling back to local factsheet retrieval for this answer."
