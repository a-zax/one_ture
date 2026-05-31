from __future__ import annotations

import re
import sqlite3

import pandas as pd

from .settings import DATA_DIR


DB_PATH = DATA_DIR / "customers.db"
CUSTOMERS_CSV = DATA_DIR / "customers.csv"
HOLDINGS_CSV = DATA_DIR / "holdings.csv"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    seed_database(conn)
    return conn


def seed_database(conn: sqlite3.Connection) -> None:
    customers = pd.read_csv(CUSTOMERS_CSV)
    holdings = pd.read_csv(HOLDINGS_CSV)
    customers.to_sql("customers", conn, if_exists="replace", index=False)
    holdings.to_sql("holdings", conn, if_exists="replace", index=False)
    conn.commit()


def find_customer_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE lower(email) = lower(?)",
            (email.strip(),),
        ).fetchone()
        return dict(row) if row else None


def fetch_customer_profile(customer_id: str) -> tuple[dict | None, list[dict]]:
    with get_connection() as conn:
        customer = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        holdings = conn.execute(
            "SELECT * FROM holdings WHERE customer_id = ?",
            (customer_id,),
        ).fetchall()

    customer_data = dict(customer) if customer else None
    holding_rows = [dict(row) for row in holdings]
    return customer_data, holding_rows


def get_customer_context(customer_id: str) -> str:
    customer_dict, holdings = fetch_customer_profile(customer_id)

    if not customer_dict:
        return "No customer record found."

    lines = [
        f"Customer name: {customer_dict['name']}",
        f"Email: {customer_dict['email']}",
        f"Folio number: {customer_dict['folio_number']}",
        f"Masked PAN: {customer_dict['pan_masked']}",
        f"Masked phone: {customer_dict['phone_masked']}",
        f"Risk profile: {customer_dict['risk_profile']}",
        f"Total invested amount: Rs. {customer_dict['total_invested']}",
        f"Current portfolio value: Rs. {customer_dict['current_value']}",
        f"SIP amount: Rs. {customer_dict['sip_amount']}",
        f"Last transaction: {customer_dict['last_transaction']}",
        "",
        "Holdings:",
    ]

    for item in holdings:
        lines.append(
            "- {scheme} ({category}): units {units}, NAV {nav}, invested Rs. {invested}, current value Rs. {value}".format(
                scheme=item["scheme_name"],
                category=item["category"],
                units=item["units"],
                nav=item["nav"],
                invested=item["invested_amount"],
                value=item["current_value"],
            )
        )

    return "\n".join(lines)


def answer_customer_query(query: str, customer_id: str) -> str:
    context = get_customer_context(customer_id)
    requested_items = get_requested_customer_fields(query.lower(), context)

    if len(requested_items) == 1:
        return requested_items[0][1]

    if requested_items:
        lines = ["Here are the requested customer details after successful 2FA:"]
        for label, answer in requested_items:
            lines.append(f"\n**{label}**\n{answer}")
        return "\n".join(lines)

    return "Here is the customer summary after successful 2FA:\n\n" + context


def get_requested_customer_fields(query: str, context: str) -> list[tuple[str, str]]:
    requested: list[tuple[str, str]] = []
    added_labels: set[str] = set()

    def add(label: str, answer: str) -> None:
        if label not in added_labels:
            requested.append((label, answer))
            added_labels.add(label)

    if "value" in query or "portfolio" in query or "balance" in query:
        add("Current portfolio value", _extract_line(context, "Current portfolio value"))

    if re.search(r"\bfolio\b", query):
        add("Folio number", _extract_line(context, "Folio number"))

    if "holding" in query or "which scheme" in query or "schemes am i" in query or "invested in" in query:
        add("Holdings", _extract_holdings(context))

    if "sip" in query:
        add("SIP amount", _extract_line(context, "SIP amount"))

    if "last transaction" in query or "transaction" in query:
        add("Last transaction", _extract_line(context, "Last transaction"))

    if "risk" in query:
        add("Risk profile", _extract_line(context, "Risk profile"))

    if "pan" in query:
        add("Masked PAN", _extract_line(context, "Masked PAN"))

    if "phone" in query or "mobile" in query or "registered phone" in query:
        add("Registered phone", _extract_line(context, "Masked phone"))

    if re.search(r"how much.*invested|total invested|invested amount", query):
        add("Total invested amount", _extract_line(context, "Total invested amount"))

    return requested


def _extract_line(context: str, prefix: str) -> str:
    for line in context.splitlines():
        if line.startswith(prefix):
            return line
    return "The requested customer detail is not available in the customer records."


def _extract_holdings(context: str) -> str:
    if "Holdings:" not in context:
        return "No holdings are available for this customer."
    return context.split("Holdings:", 1)[1].strip()
