from fastmcp import FastMCP
import os
import sqlite3

# Use safe path handling
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

mcp = FastMCP("ExpenseTracker")

# ----------------------
# Initialize database
# ----------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        conn.commit()  # Ensure table creation is saved

init_db()

# ----------------------
# Tools
# ----------------------
@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()             # Use a proper cursor
        cur.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        conn.commit()                   # <-- Important: commit to save data
        return {"status": "ok", "id": cur.lastrowid}

@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List expense entries within an inclusive date range."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
            """,
            (start_date, end_date)
        )
        return [dict(row) for row in cur.fetchall()]

@mcp.tool()
def summarize(start_date: str, end_date: str, category: str = None):
    """Summarize expenses by category within an inclusive date range."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Return categories from JSON file."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ----------------------
# Run MCP server
# ----------------------
if __name__ == "__main__":
    mcp.run()

