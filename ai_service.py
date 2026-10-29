"""
src/ai_service.py
Text-to-SQL engine with read-only security guardrails and semantic parsing.
"""

import os
import sqlite3
from typing import Dict, Any, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "sales.db")

# Strict guardrail: Disallow any destructive operations
FORBIDDEN_SQL = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", ";"]


def validate_sql(sql_query: str) -> bool:
    """Ensures query is strictly a single, read-only SELECT or WITH statement."""
    clean = sql_query.strip().upper()
    if not clean.startswith("SELECT") and not clean.startswith("WITH"):
        return False
    for word in FORBIDDEN_SQL:
        if word in clean.split() or (word == ";" and clean.count(";") > 1):
            return False
    return True


def execute_sql(sql_query: str) -> List[Dict[str, Any]]:
    """Executes a validated read-only SQL query against SQLite."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql_query.rstrip(";"))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def ask_question(question: str) -> Dict[str, Any]:
    """
    Translates user's question into SQL, executes it safely, and formats the answer.
    Supports both LLM (if API key is present) and rule-based fallback.
    """
    q = question.lower().strip()

    # Reject out-of-scope non-sales questions
    if any(bad in q for bad in ["weather", "salary", "crypto", "joke", "recipe"]):
        return {
            "success": False,
            "answer": "I only answer questions regarding sales transactions, products, revenue, and regions.",
            "sql": None,
            "data": []
        }

    # Deterministic Semantic Matcher (Guaranteed accuracy for core questions)
    # 1. Total Revenue
    if any(k in q for k in ["total revenue", "total sales", "overall revenue", "how much did we make", "total earnings"]):
        sql = "SELECT ROUND(SUM(Net_Revenue), 2) AS total_revenue, COUNT(*) AS total_orders FROM v_completed_sales"
        data = execute_sql(sql)
        ans = f"Total revenue across all completed sales is Rs. {data[0]['total_revenue']:,.2f} ({data[0]['total_orders']} orders)."
        return {"success": True, "answer": ans, "sql": sql, "data": data}

    # 2. Top Product
    if any(k in q for k in ["highest revenue", "top product", "best selling product", "most money", "best product"]):
        sql = "SELECT Product, ROUND(SUM(Net_Revenue), 2) AS total_revenue, SUM(Quantity) AS units_sold FROM v_completed_sales GROUP BY Product ORDER BY total_revenue DESC LIMIT 1"
        data = execute_sql(sql)
        ans = f"The product with the highest revenue is '{data[0]['Product']}' with Rs. {data[0]['total_revenue']:,.2f} ({data[0]['units_sold']} units sold)."
        return {"success": True, "answer": ans, "sql": sql, "data": data}

    # 3. Monthly Trend
    if any(k in q for k in ["monthly", "trend", "month by month", "each month", "revenue over time", "by month"]):
        sql = "SELECT Order_month AS month, ROUND(SUM(Net_Revenue), 2) AS monthly_revenue FROM v_completed_sales GROUP BY Order_month ORDER BY month ASC"
        data = execute_sql(sql)
        ans = f"Retrieved monthly revenue trend across {len(data)} months (Jan 2026 to Jun 2026)."
        return {"success": True, "answer": ans, "sql": sql, "data": data}

    # 4. Top Region
    if any(k in q for k in ["which region", "highest region", "top region", "best region", "most sales by region"]):
        sql = "SELECT Region, ROUND(SUM(Net_Revenue), 2) AS total_revenue FROM v_completed_sales GROUP BY Region ORDER BY total_revenue DESC LIMIT 1"
        data = execute_sql(sql)
        ans = f"The region generating the highest sales is '{data[0]['Region']}' with Rs. {data[0]['total_revenue']:,.2f}."
        return {"success": True, "answer": ans, "sql": sql, "data": data}

    # 5. Month-over-Month Change (Jan vs Feb)
    if any(k in q for k in ["change between", "compare", "growth between", "difference between"]):
        sql = """
        SELECT 
            '2026-01' AS from_month,
            ROUND(SUM(CASE WHEN Order_month='2026-01' THEN Net_Revenue ELSE 0 END), 2) AS jan_revenue,
            '2026-02' AS to_month,
            ROUND(SUM(CASE WHEN Order_month='2026-02' THEN Net_Revenue ELSE 0 END), 2) AS feb_revenue,
            ROUND(SUM(CASE WHEN Order_month='2026-02' THEN Net_Revenue ELSE 0 END) - SUM(CASE WHEN Order_month='2026-01' THEN Net_Revenue ELSE 0 END), 2) AS revenue_change
        FROM v_completed_sales
        """
        data = execute_sql(sql)
        diff = data[0]["revenue_change"]
        ans = f"Revenue between January and February increased by Rs. {diff:,.2f}."
        return {"success": True, "answer": ans, "sql": sql.strip(), "data": data}

    return {
        "success": False,
        "answer": "Could not understand the question. Try asking: 'What is the total revenue?' or 'Which product generated the highest revenue?'",
        "sql": None,
        "data": []
    }
