from __future__ import annotations


CUSTOMER_TERMS = {
    "my",
    "me",
    "mine",
    "account",
    "folio",
    "portfolio",
    "holding",
    "holdings",
    "investment value",
    "current value",
    "sip amount",
    "last transaction",
    "pan",
    "phone",
    "registered email",
    "invested in",
    "schemes",
}

DIRECT_CUSTOMER_TERMS = {"folio", "customer id", "my sip", "my portfolio", "my holdings"}
FIRST_PERSON_WORDS = {"i", "my", "me", "mine"}


def classify_query(query: str) -> str:
    text = query.lower().strip()
    if not text:
        return "empty"

    words = set(text.split())
    has_first_person_word = bool(words & FIRST_PERSON_WORDS)
    mentions_customer_data = any(term in text for term in CUSTOMER_TERMS)

    if has_first_person_word and mentions_customer_data:
        return "customer"
    if any(term in text for term in DIRECT_CUSTOMER_TERMS):
        return "customer"

    return "document"
