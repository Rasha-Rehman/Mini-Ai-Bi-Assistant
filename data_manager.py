"""
src/data_manager.py
Cleans sales data, handles anomalies/missing values, and populates SQLite.
"""

import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "sales_data.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "sales.db")


def load_and_clean_data(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """Reads CSV, fixes missing values, standardizes dates, and computes revenue."""
    df = pd.read_csv(csv_path)

    # 1. Clean whitespace from headers and text columns
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # 2. Fix missing Unit_price (Row TXN0051 Laptop Stand): impute with catalog median
    df["Unit_price"] = pd.to_numeric(df["Unit_price"], errors="coerce")
    laptop_stand_price = df[df["Product"] == "Laptop Stand"]["Unit_price"].median()
    df["Unit_price"] = df["Unit_price"].fillna(laptop_stand_price)

    # 3. Clean numeric fields
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).astype(int)
    df["Discount_amount"] = pd.to_numeric(df["Discount_amount"], errors="coerce").fillna(0.0)

    # 4. Standardize dates to ISO format (YYYY-MM-DD) so SQLite can sort and group months
    df["Order_date"] = pd.to_datetime(df["Order_date"], format="%d-%m-%Y").dt.strftime("%Y-%m-%d")
    df["Order_month"] = pd.to_datetime(df["Order_date"]).dt.strftime("%Y-%m")

    # 5. Compute Net Revenue = (Quantity * Price) - Discount
    df["Net_Revenue"] = (df["Quantity"] * df["Unit_price"]) - df["Discount_amount"]

    return df


def setup_database():
    """Saves cleaned data into SQLite and creates an analytical view."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    df = load_and_clean_data()
    conn = sqlite3.connect(DB_PATH)

    # Save to 'sales' table
    df.to_sql("sales", conn, if_exists="replace", index=False)

    # Create indices for fast querying
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(Order_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_prod ON sales(Product)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_region ON sales(Region)")

    # Create analytical view filtering only valid completed sales
    cursor.execute("DROP VIEW IF EXISTS v_completed_sales")
    cursor.execute("""
        CREATE VIEW v_completed_sales AS
        SELECT * FROM sales
        WHERE LOWER(Status) = 'completed' AND Quantity > 0;
    """)
    conn.commit()
    conn.close()
    print("Database setup complete! Cleaned data saved to data/sales.db")


if __name__ == "__main__":
    setup_database()
