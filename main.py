from fastmcp import FastMCP
import os
import sqlite3
import aiosqlite
import tempfile
import json
import sys


# ============================================================
# Configuration
# ============================================================

# Use a writable temporary directory
TEMP_DIR = tempfile.gettempdir()

# Store SQLite database in the writable temp directory
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# categories.json remains alongside the application
CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

print(
    f"Database path: {DB_PATH}",
    file=sys.stderr
)


# ============================================================
# FastMCP Server
# ============================================================

mcp = FastMCP("ExpenseTracker")


# ============================================================
# Database Initialization
# ============================================================

def init_db():
    """Initialize the SQLite database."""

    try:
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

            conn.commit()

        print(
            "Database initialized successfully",
            file=sys.stderr
        )

    except Exception as e:

        print(
            f"Database initialization error: {e}",
            file=sys.stderr
        )

        raise


init_db()


# ============================================================
# Add Expense
# ============================================================

@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
) -> dict:
    """
    Add a new expense entry to the database.

    Args:
        date: Expense date in YYYY-MM-DD format.
        amount: Expense amount.
        category: Expense category.
        subcategory: Optional expense subcategory.
        note: Optional note about the expense.

    Returns:
        Information about the newly created expense.
    """

    try:

        async with aiosqlite.connect(DB_PATH) as conn:

            cursor = await conn.execute(
                """
                INSERT INTO expenses
                (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                )
            )

            expense_id = cursor.lastrowid

            await conn.commit()

            return {
                "status": "success",
                "id": expense_id,
                "message": "Expense added successfully"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


# ============================================================
# List Expenses
# ============================================================

@mcp.tool()
async def list_expenses(
    start_date: str,
    end_date: str
) -> list[dict]:
    """
    List expenses within an inclusive date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        List of expense records.
    """

    try:

        async with aiosqlite.connect(DB_PATH) as conn:

            cursor = await conn.execute(
                """
                SELECT
                    id,
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (
                    start_date,
                    end_date
                )
            )

            rows = await cursor.fetchall()

            columns = [
                description[0]
                for description in cursor.description
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:

        return [
            {
                "status": "error",
                "message": f"Error listing expenses: {str(e)}"
            }
        ]


# ============================================================
# Summarize Expenses
# ============================================================

@mcp.tool()
async def summarize(
    start_date: str,
    end_date: str,
    category: str | None = None
) -> list[dict]:
    """
    Summarize expenses by category.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        category: Optional category filter.

    Returns:
        Expense totals grouped by category.
    """

    try:

        async with aiosqlite.connect(DB_PATH) as conn:

            query = """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """

            params = [
                start_date,
                end_date
            ]

            if category:

                query += """
                    AND category = ?
                """

                params.append(category)

            query += """
                GROUP BY category
                ORDER BY total_amount DESC
            """

            cursor = await conn.execute(
                query,
                params
            )

            rows = await cursor.fetchall()

            columns = [
                description[0]
                for description in cursor.description
            ]

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    except Exception as e:

        return [
            {
                "status": "error",
                "message": f"Error summarizing expenses: {str(e)}"
            }
        ]


# ============================================================
# Categories Resource
# ============================================================

@mcp.resource(
    "expense://categories",
    mime_type="application/json"
)
def categories() -> str:
    """
    Return available expense categories.
    """

    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other"
        ]
    }

    try:

        with open(
            CATEGORIES_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except FileNotFoundError:

        return json.dumps(
            default_categories,
            indent=2
        )

    except Exception as e:

        return json.dumps({
            "error": f"Could not load categories: {str(e)}"
        })


# ============================================================
# Start Server
# ============================================================

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )