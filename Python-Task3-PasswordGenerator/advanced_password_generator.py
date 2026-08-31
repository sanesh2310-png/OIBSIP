"""
Advanced-Tier Random Password Generator (GUI)
------------------------------------------------
Includes all Beginner-tier features (length control, character-type
selection, at-least-2-types validation) plus:
  - tkinter GUI — spinbox for length, checkboxes for character types
  - Uses the `secrets` module (cryptographically secure), never `random`
  - Password strength indicator (Weak / Medium / Strong)
  - Guarantees at least one character from each selected type
  - "Copy to Clipboard" button using pyperclip (auto-copies on generation)
  - Option to exclude ambiguous characters (0, O, l, 1, I)
  - Generation history: last 5 passwords shown in-session only
    (never written to disk, for security)

Install:
    pip install pyperclip

(tkinter and secrets ship with standard Python — no separate install needed.
 On some Linux distros: sudo apt-get install python3-tk)

Run:
    python advanced_password_generator.py
"""

import secrets
import string
import tkinter as tk
from tkinter import messagebox, ttk

import pyperclip

AMBIGUOUS_CHARS = "0Ol1I"

MAX_HISTORY = 5


# ---------------------------------------------------------------------------
# Core password logic (kept separate from the GUI so it's easy to test/reuse)
# ---------------------------------------------------------------------------

def build_pools(use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous):
    """Build the character pool for each selected type, optionally
    stripping ambiguous characters. Returns a dict of type -> pool string,
    containing only the types that were actually selected."""
    pools = {}

    if use_upper:
        pools["upper"] = string.ascii_uppercase
    if use_lower:
        pools["lower"] = string.ascii_lowercase
    if use_digits:
        pools["digits"] = string.digits
    if use_symbols:
        pools["symbols"] = string.punctuation

    if exclude_ambiguous:
        for key in pools:
            pools[key] = "".join(c for c in pools[key] if c not in AMBIGUOUS_CHARS)

    # Guard against a pool becoming empty after stripping ambiguous chars
    # (e.g. digits-only with ambiguous excluded could get thin, but not empty
    # here since only 0/1 are digits in AMBIGUOUS_CHARS — still, be safe)
    return {k: v for k, v in pools.items() if v}


def generate_secure_password(length, use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous):
    """
    Generate a cryptographically secure password using `secrets`.
    Guarantees at least one character from each selected type.
    Raises ValueError with a helpful message if the request is invalid.
    """
    pools = build_pools(use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous)

    if len(pools) < 2:
        raise ValueError("Please select at least 2 character types.")

    if length < 8:
        raise ValueError("Length must be at least 8 characters.")

    if length < len(pools):
        raise ValueError(f"Length must be at least {len(pools)} to include one of each selected type.")

    combined_pool = "".join(pools.values())

    # Step 1: guarantee at least one char from each selected type
    password_chars = [secrets.choice(pool) for pool in pools.values()]

    # Step 2: fill the rest randomly (securely) from the combined pool
    remaining = length - len(password_chars)
    password_chars += [secrets.choice(combined_pool) for _ in range(remaining)]

    # Step 3: shuffle securely so the guaranteed chars aren't always at the front
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def assess_strength(password: str, type_count: int) -> str:
    """
    Simple heuristic: combine length and character-type diversity.
    Returns 'Weak', 'Medium', or 'Strong'.
    """
    length = len(password)

    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    score += type_count  # 2..4 selected types

    if score <= 3:
        return "Weak"
    elif score <= 5:
        return "Medium"
    else:
        return "Strong"


STRENGTH_COLORS = {
    "Weak": "#ef4444",     # red
    "Medium": "#f59e0b",   # orange
    "Strong": "#22c55e",   # green
}


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class PasswordGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Generator")
        self.geometry("460x620")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        self.history = []  # last MAX_HISTORY generated passwords, this session only

        self._build_widgets()

    # ---- UI construction ----

    def _build_widgets(self):
        pad = {"padx": 12, "pady": 6}

        title = tk.Label(self, text="Password Generator", font=("Segoe UI", 18, "bold"), bg="#f8fafc")
        title.pack(pady=(16, 10))

        # --- Length control ---
        length_frame = tk.Frame(self, bg="#f8fafc")
        length_frame.pack(**pad)
        tk.Label(length_frame, text="Password length:", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        self.length_var = tk.IntVar(value=12)
        self.length_spin = tk.Spinbox(length_frame, from_=8, to=64, textvariable=self.length_var, width=6, font=("Segoe UI", 11))
        self.length_spin.grid(row=0, column=1, padx=10)

        # --- Character type checkboxes ---
        types_frame = tk.LabelFrame(self, text="Character types (choose at least 2)", bg="#f8fafc", font=("Segoe UI", 10, "bold"))
        types_frame.pack(fill="x", padx=20, pady=10)

        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=False)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)

        tk.Checkbutton(types_frame, text="Uppercase (A-Z)", variable=self.upper_var, bg="#f8fafc").pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(types_frame, text="Lowercase (a-z)", variable=self.lower_var, bg="#f8fafc").pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(types_frame, text="Numbers (0-9)", variable=self.digits_var, bg="#f8fafc").pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(types_frame, text="Symbols (!@#$...)", variable=self.symbols_var, bg="#f8fafc").pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(types_frame, text="Exclude ambiguous characters (0, O, l, 1, I)", variable=self.exclude_ambiguous_var, bg="#f8fafc").pack(anchor="w", padx=10, pady=(8, 2))

        # --- Generate button ---
        gen_btn = tk.Button(
            self, text="Generate Password", font=("Segoe UI", 11, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8",
            command=self.on_generate, width=20, bd=0, cursor="hand2"
        )
        gen_btn.pack(pady=10)

        # --- Result display ---
        self.result_var = tk.StringVar(value="")
        result_entry = tk.Entry(self, textvariable=self.result_var, font=("Consolas", 13), justify="center", state="readonly", readonlybackground="white")
        result_entry.pack(fill="x", padx=20, pady=(0, 6))

        # --- Strength indicator ---
        self.strength_frame = tk.Frame(self, bg="#e5e7eb", height=28)
        self.strength_frame.pack(fill="x", padx=20, pady=(0, 6))
        self.strength_frame.pack_propagate(False)
        self.strength_label = tk.Label(self.strength_frame, text="Strength: —", bg="#e5e7eb", font=("Segoe UI", 10, "bold"))
        self.strength_label.pack(expand=True)

        # --- Copy button ---
        copy_btn = tk.Button(
            self, text="Copy to Clipboard", font=("Segoe UI", 10),
            command=self.on_copy, cursor="hand2"
        )
        copy_btn.pack(pady=(0, 10))

        # --- History ---
        history_label = tk.Label(self, text="Last 5 passwords this session:", bg="#f8fafc", font=("Segoe UI", 10, "bold"))
        history_label.pack(pady=(6, 2))

        self.history_listbox = tk.Listbox(self, height=5, font=("Consolas", 10), justify="center")
        self.history_listbox.pack(fill="x", padx=20, pady=(0, 10))

        note = tk.Label(
            self,
            text="History is kept only in memory for this session\nand is never saved to disk.",
            font=("Segoe UI", 8), bg="#f8fafc", fg="#6b7280", justify="center"
        )
        note.pack()

    # ---- Event handlers ----

    def on_generate(self):
        try:
            length = int(self.length_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid Input", "Length must be a whole number.")
            return

        try:
            password = generate_secure_password(
                length=length,
                use_upper=self.upper_var.get(),
                use_lower=self.lower_var.get(),
                use_digits=self.digits_var.get(),
                use_symbols=self.symbols_var.get(),
                exclude_ambiguous=self.exclude_ambiguous_var.get(),
            )
        except ValueError as e:
            messagebox.showerror("Invalid Selection", str(e))
            return

        type_count = sum([
            self.upper_var.get(), self.lower_var.get(),
            self.digits_var.get(), self.symbols_var.get()
        ])
        strength = assess_strength(password, type_count)

        self.result_var.set(password)
        self.strength_label.configure(
            text=f"Strength: {strength}",
            bg=STRENGTH_COLORS[strength], fg="white"
        )
        self.strength_frame.configure(bg=STRENGTH_COLORS[strength])

        # Auto-copy to clipboard on generation
        try:
            pyperclip.copy(password)
        except pyperclip.PyperclipException:
            pass  # clipboard may be unavailable in some environments; generation still succeeds

        # Update in-memory history (most recent first, max 5, never persisted)
        self.history.insert(0, password)
        self.history = self.history[:MAX_HISTORY]
        self._refresh_history_display()

    def on_copy(self):
        password = self.result_var.get()
        if not password:
            messagebox.showinfo("Nothing to Copy", "Generate a password first.")
            return
        try:
            pyperclip.copy(password)
            messagebox.showinfo("Copied", "Password copied to clipboard.")
        except pyperclip.PyperclipException:
            messagebox.showerror("Clipboard Error", "Could not access the system clipboard.")

    def _refresh_history_display(self):
        self.history_listbox.delete(0, tk.END)
        for pwd in self.history:
            self.history_listbox.insert(tk.END, pwd)


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()
