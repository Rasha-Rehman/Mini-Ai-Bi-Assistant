# Mini AI Business Intelligence Assistant

An AI-powered Business Intelligence (BI) assistant built for the **Graduate Engineer Trainee (GET) Selection Challenge**. It enables business users to ask sales performance questions in plain English and receive accurate, deterministic answers backed by real database queries.

---

## 🏗️ Architecture Overview

The system follows a **Vectorless RAG (Text-to-SQL)** pattern. Instead of using a vector database for numbers (which causes mathematical hallucinations), the AI translates natural language into verified SQL queries executed directly against an SQLite database.

![System Architecture](architecture_diagram.png)

```
[ Business User ]
       │
       ▼  (Plain English Question: "What is the total revenue?")
[ User Interface ]  (Streamlit: app.py)
       │
       ▼
[ AI Service & Guardrails ]  (ai_service.py)
       │ ── Generates SQL (LLM / Semantic Parser)
       │ ── Validates query safety (SELECT only, blocks DROP/DELETE)
       ▼
[ SQLite Reference Database ]  (data/sales.db)
       │ ── Mode: URI read-only (?mode=ro)
       │ ── View: v_completed_sales (Excludes returns, Net_Revenue = Qty*Price - Discount)
       ▼
[ Answer & Supporting Data Table Returned to User ]
```

---

## 📁 Simple Project Structure

```text
sales_bi_assistant/
├── data/
│   ├── sales_data.csv                 # Raw 51 sales transaction records
│   └── sales.db                       # Cleaned SQLite reference database
├── data_manager.py                    # Step 1: Cleans CSV and loads into SQLite (35 lines)
├── ai_service.py                      # Step 2: Safe Text-to-SQL engine & guardrails (70 lines)
├── app.py                             # Step 3: Streamlit interactive web interface (50 lines)
├── test_app.py                        # Step 4: 5 automated test cases (40 lines)
├── architecture_diagram.png           # Deliverable #3: Professional architecture image
├── AI_Assisted_Development_Report.docx # Deliverable #5: Microsoft Word reflection document
├── README.md                          # Deliverable #2: Setup & execution instructions
└── INTERVIEW_PREPARATION_GUIDE.md     # Technical interview preparation cheat-sheet
```

---

## 🚀 Setup & Execution Instructions

### 1. Prerequisites
Ensure you have **Python 3.10+** installed. Install the required dependencies:

```bash
pip install pandas streamlit pytest google-generativeai
```

---

### 2. Step 1: Initialize & Clean the Database
Run the data manager script to ingest the CSV, impute missing values, and populate the SQLite database:

```bash
python data_manager.py
```
*Output: `Database setup complete! Cleaned data saved to data/sales.db`*

---

### 3. Step 2: Run the Automated Tests
Run the automated test suite to verify that all functional requirements, edge cases, and security checks pass:

```bash
python -m pytest test_app.py -v
```

**Expected Test Output:**
```text
test_app.py::test_edge_case_missing_data PASSED                          [ 20%]
test_app.py::test_valid_total_revenue PASSED                             [ 40%]
test_app.py::test_valid_top_product PASSED                               [ 60%]
test_app.py::test_invalid_question PASSED                                [ 80%]
test_app.py::test_security_blocks_destructive_sql PASSED                 [100%]

============================== 5 passed in 0.87s ==============================
```

---

### 4. Step 3: Launch the Interactive Web App
Start the Streamlit user interface:

```bash
python -m streamlit run app.py
```

* Your browser will automatically open at `http://localhost:8501`.
* You can click the quick-action buttons (**💰 Total Revenue**, **🏆 Top Product**, **📈 Monthly Trend**, **🌍 Top Region**) or type custom sales questions into the search box.

---

## 📊 Core Questions & Grounded Results

All analytics are computed deterministically against the provided reference sales data:

| # | Business Question | Deterministic SQL Logic | Result in Dataset |
| :--- | :--- | :--- | :--- |
| **1** | **What is the total revenue?** | `SELECT ROUND(SUM(Net_Revenue), 2) FROM v_completed_sales` | **Rs. 1,445,200.00** (49 orders) |
| **2** | **Which product generated highest revenue?** | `GROUP BY Product ORDER BY total_revenue DESC LIMIT 1` | **Monitor** (Rs. 473,000.00 / 50 units) |
| **3** | **What is the monthly revenue trend?** | `GROUP BY Order_month ORDER BY month ASC` | 6 Months (Jan: 210k to Jun: 217k) |
| **4** | **Which region generated highest sales?** | `GROUP BY Region ORDER BY total_revenue DESC LIMIT 1` | **South** (Rs. 411,200.00) |
| **5** | **Revenue change between Jan and Feb?** | Month comparison delta | **+Rs. 24,350.00 (+11.58%)** |

---

## 🧹 Data Cleaning & Anomaly Handling

The data loader (`data_manager.py`) automatically resolves intentional anomalies in the raw CSV:

1. **Missing Unit Price (`TXN0051`)**:
   * *Problem:* `TXN0051` had a blank unit price for *Laptop Stand*.
   * *Fix:* Imputed with the catalog median for *Laptop Stand* (`Rs. 1,200.00`).
2. **Returned Orders (`TXN0033`)**:
   * *Problem:* `TXN0033` has status `Returned`. Including returns inflates revenue.
   * *Fix:* Filtered out via the SQL view `v_completed_sales` (`WHERE LOWER(Status) = 'completed'`).
3. **Zero-Quantity Orders (`TXN0034`)**:
   * *Problem:* Order had `0` quantity.
   * *Fix:* Handled safely without zero-division errors.
4. **Discounts Deducted**:
   * Applied accounting formula: `Net_Revenue = (Quantity * Unit_price) - Discount_amount`.
5. **Date Normalization**:
   * Converted `DD-MM-YYYY` human dates to ISO `YYYY-MM-DD` so SQLite can sort and group months chronologically.

---

## 🛡️ Security Guardrails & Safe AI

* **Read-Only Enforcement:** Queries must strictly start with `SELECT` or `WITH`.
* **Destructive SQL Blocking:** Rejects any query containing `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, or `TRUNCATE`.
* **Engine-Level Protection:** Database connections are opened in read-only URI mode (`file:data/sales.db?mode=ro`).
* **Anti-Hallucination:** Non-sales questions (e.g. weather, general knowledge) are refused politely rather than inventing fake data.

---

## ⚠️ Known Limitations

* **Fuzzy Misspelling Matching:** Misspelled product names (e.g. *"monitr"*) in offline mode require exact keyword matches; handled automatically when an LLM API key is provided.
* **Stateless Memory:** Each question is processed independently; multi-turn conversational follow-ups (e.g., *"What about the previous month?"*) are planned for future versions.
