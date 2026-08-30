"""
Advanced-Tier BMI Calculator (GUI)
------------------------------------
Includes all Beginner-tier logic (BMI formula, category classification,
input validation) plus:
  - tkinter GUI — labeled input fields, a Calculate button, no CLI
  - Colour-coded result feedback (blue/green/orange/red by category)
  - Multi-user support — enter a name to save/load records per user
  - Historical records stored in an SQLite database (bmi_records.db)
  - Graph view — matplotlib line chart of a user's BMI trend over time
  - Error handling for database read/write failures

Install:
    pip install matplotlib

(tkinter and sqlite3 ship with standard Python — no separate install needed.
 On some Linux distros you may need: sudo apt-get install python3-tk)

Run:
    python advanced_bmi.py
"""

import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

DB_PATH = "bmi_records.db"


# ---------------------------------------------------------------------------
# Data layer — SQLite persistence
# ---------------------------------------------------------------------------

class BMIDatabase:
    """Handles all reads/writes to the SQLite database, with error handling
    so a database problem shows a message box instead of crashing the app."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_name TEXT NOT NULL,
                        weight_kg REAL NOT NULL,
                        height_m REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not initialize database:\n{e}")

    def add_record(self, user_name, weight, height, bmi, category):
        try:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO records
                       (user_name, weight_kg, height_m, bmi, category, recorded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_name, weight, height, bmi, category,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save record:\n{e}")
            return False

    def get_records_for_user(self, user_name):
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """SELECT bmi, recorded_at FROM records
                       WHERE user_name = ? ORDER BY recorded_at ASC""",
                    (user_name,),
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not read records:\n{e}")
            return []

    def get_all_user_names(self):
        try:
            with self._connect() as conn:
                cursor = conn.execute("SELECT DISTINCT user_name FROM records ORDER BY user_name")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not read user list:\n{e}")
            return []


# ---------------------------------------------------------------------------
# BMI logic (same formula/categories as the beginner tier)
# ---------------------------------------------------------------------------

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


CATEGORY_COLORS = {
    "Underweight": "#3b82f6",  # blue
    "Normal": "#22c55e",       # green
    "Overweight": "#f59e0b",   # orange
    "Obese": "#ef4444",        # red
}


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        self.db = BMIDatabase()

        self._build_widgets()

    # ---- UI construction ----

    def _build_widgets(self):
        pad = {"padx": 12, "pady": 6}

        title = tk.Label(self, text="BMI Calculator", font=("Segoe UI", 18, "bold"), bg="#f8fafc")
        title.pack(pady=(16, 8))

        form = tk.Frame(self, bg="#f8fafc")
        form.pack(**pad)

        tk.Label(form, text="Name:", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", **pad)
        self.name_entry = tk.Entry(form, width=20, font=("Segoe UI", 11))
        self.name_entry.grid(row=0, column=1, **pad)

        tk.Label(form, text="Weight (kg):", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", **pad)
        self.weight_entry = tk.Entry(form, width=20, font=("Segoe UI", 11))
        self.weight_entry.grid(row=1, column=1, **pad)

        tk.Label(form, text="Height (m):", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="e", **pad)
        self.height_entry = tk.Entry(form, width=20, font=("Segoe UI", 11))
        self.height_entry.grid(row=2, column=1, **pad)

        calc_btn = tk.Button(
            self, text="Calculate", font=("Segoe UI", 11, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8",
            command=self.on_calculate, width=18, height=1, bd=0, cursor="hand2"
        )
        calc_btn.pack(pady=10)

        self.result_frame = tk.Frame(self, bg="#e5e7eb", width=380, height=70)
        self.result_frame.pack(pady=6)
        self.result_frame.pack_propagate(False)

        self.result_label = tk.Label(
            self.result_frame, text="Enter your details and press Calculate",
            font=("Segoe UI", 12, "bold"), bg="#e5e7eb", fg="#374151", wraplength=340
        )
        self.result_label.pack(expand=True)

        graph_btn = tk.Button(
            self, text="View BMI Trend Graph", font=("Segoe UI", 10),
            bg="#f8fafc", command=self.show_trend_graph, cursor="hand2"
        )
        graph_btn.pack(pady=(14, 4))

        hint = tk.Label(
            self,
            text="Records are saved per name.\nEnter the same name again to build a history.",
            font=("Segoe UI", 9), bg="#f8fafc", fg="#6b7280", justify="center"
        )
        hint.pack(pady=(4, 0))

    # ---- Event handlers ----

    def on_calculate(self):
        name = self.name_entry.get().strip()
        weight_raw = self.weight_entry.get().strip()
        height_raw = self.height_entry.get().strip()

        if not name:
            messagebox.showwarning("Missing Name", "Please enter a name so your record can be saved.")
            return

        try:
            weight = float(weight_raw)
            height = float(height_raw)
        except ValueError:
            messagebox.showerror("Invalid Input", "Weight and height must be numbers (e.g. 70 or 1.75).")
            return

        if weight <= 0 or height <= 0:
            messagebox.showerror("Invalid Input", "Weight and height must be positive numbers greater than zero.")
            return

        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)
        color = CATEGORY_COLORS[category]

        self.result_frame.configure(bg=color)
        self.result_label.configure(
            bg=color, fg="white",
            text=f"BMI: {bmi:.2f}\nCategory: {category}"
        )

        self.db.add_record(name, weight, height, bmi, category)

    def show_trend_graph(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Enter a name first, then press 'View BMI Trend Graph'.")
            return

        records = self.db.get_records_for_user(name)
        if not records:
            messagebox.showinfo("No Records", f"No saved BMI history found for '{name}' yet.\nCalculate at least once to start a history.")
            return

        bmis = [row[0] for row in records]
        timestamps = [row[1] for row in records]

        graph_window = tk.Toplevel(self)
        graph_window.title(f"BMI Trend — {name}")
        graph_window.geometry("600x450")

        fig = Figure(figsize=(6, 4.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(range(len(bmis)), bmis, marker="o", color="#2563eb")
        ax.set_title(f"BMI Trend for {name}")
        ax.set_xlabel("Record #")
        ax.set_ylabel("BMI")
        ax.set_xticks(range(len(bmis)))
        ax.set_xticklabels([t.split(" ")[0] for t in timestamps], rotation=45, ha="right", fontsize=8)
        ax.axhspan(18.5, 25, color="#22c55e", alpha=0.08)
        ax.grid(True, linestyle="--", alpha=0.4)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BMIApp()
    app.mainloop()
