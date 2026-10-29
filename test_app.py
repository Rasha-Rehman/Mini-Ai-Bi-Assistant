"""
test_app.py
5 automated test cases covering valid questions, invalid questions, and edge cases.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from data_manager import load_and_clean_data, setup_database
from ai_service import ask_question, validate_sql

# Ensure database is set up
setup_database()


def test_edge_case_missing_data():
    """Edge Case: Verifies missing unit price for TXN0051 (Laptop Stand) is imputed."""
    df = load_and_clean_data()
    txn_51 = df[df["Transaction_Id"] == "TXN0051"].iloc[0]
    assert txn_51["Unit_price"] == 1200.0


def test_valid_total_revenue():
    """Valid Question: Verifies total revenue equals Rs. 1,445,200.00."""
    res = ask_question("What is the total revenue?")
    assert res["success"] is True
    assert res["data"][0]["total_revenue"] == 1445200.0


def test_valid_top_product():
    """Valid Question: Verifies Monitor is the highest-grossing product."""
    res = ask_question("Which product generated the highest revenue?")
    assert res["success"] is True
    assert res["data"][0]["Product"] == "Monitor"


def test_invalid_question():
    """Invalid Question: Verifies off-topic questions (e.g. weather) are politely refused."""
    res = ask_question("What is the weather in Hyderabad?")
    assert res["success"] is False
    assert "only answer questions regarding sales" in res["answer"]


def test_security_blocks_destructive_sql():
    """Security Guardrail: Verifies DROP TABLE is blocked."""
    assert validate_sql("DROP TABLE sales;") is False
    assert validate_sql("DELETE FROM sales;") is False
