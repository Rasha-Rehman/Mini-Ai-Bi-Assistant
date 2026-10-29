"""
src/app.py
Interactive Streamlit Web Interface for the Mini AI Business Intelligence Assistant.
"""

import sys
import os
import streamlit as st
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
from ai_service import ask_question
from data_manager import setup_database, DB_PATH

# Auto-setup database if missing
if not os.path.exists(DB_PATH):
    setup_database()

st.set_page_config(page_title="Sales AI Assistant", page_icon="📊", layout="wide")

st.title("📊 Mini AI Business Intelligence Assistant")
st.write("Ask questions about sales performance in plain English. The AI translates your question into a validated SQL query and calculates exact figures from the reference database.")

# Quick sample buttons
st.write("##### Suggested Questions:")
c1, c2, c3, c4 = st.columns(4)
q_selected = None

if c1.button("💰 Total Revenue"):
    q_selected = "What is the total revenue?"
if c2.button("🏆 Top Product"):
    q_selected = "Which product generated the highest revenue?"
if c3.button("📈 Monthly Trend"):
    q_selected = "What is the monthly revenue trend?"
if c4.button("🌍 Top Region"):
    q_selected = "Which region generated the highest sales?"

# User text input
user_question = st.text_input("Or enter your own question:", value=q_selected if q_selected else "")

if user_question:
    result = ask_question(user_question)

    if result["success"]:
        st.success(f"**Answer:** {result['answer']}")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.write("##### 📋 Supporting Data:")
            df = pd.DataFrame(result["data"])
            st.dataframe(df, use_container_width=True)

            if "monthly_revenue" in df.columns:
                st.line_chart(df.set_index("month")["monthly_revenue"])

        with col_right:
            st.write("##### 🔍 Generated SQL Query:")
            st.code(result["sql"], language="sql")
    else:
        st.error(result["answer"])
