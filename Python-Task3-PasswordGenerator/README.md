# Random Password Generator

A password generator with two tiers:

- **`beginner_password_generator.py`** — command-line tool using `random`
  and `string`. Prompts for length and character types, validates input,
  and lets you generate multiple passwords in one run.
- **`advanced_password_generator.py`** — full GUI (tkinter) using the
  cryptographically secure `secrets` module, with a strength meter,
  clipboard integration, ambiguous-character exclusion, and in-session
  history.

## Beginner Tier

**Run:**
```bash
python beginner_password_generator.py
```

No dependencies beyond the Python standard library.

- Length must be at least 8 (rejected otherwise, with a retry prompt).
- You'll be asked y/n for uppercase, lowercase, numbers, and symbols —
  at least 2 types must be chosen or it asks again.
- After each password, you can choose to generate another without
  restarting the script.

**Note:** this tier uses Python's `random` module, which is fine for
casual/learning use but is **not cryptographically secure** — that's
exactly why the advanced tier switches to `secrets`.

## Advanced Tier

**Install dependencies:**
```bash
pip install pyperclip
```
`tkinter` and `secrets` ship with standard Python. On some Linux distros,
tkinter needs a separate system package:
```bash
sudo apt-get install python3-tk
```

**Run:**
```bash
python advanced_password_generator.py
```

**How it works:**
1. Set the desired length with the spinbox (minimum 8).
2. Check which character types to include — uppercase, lowercase,
   numbers, symbols (at least 2 required).
3. Optionally check "Exclude ambiguous characters" to remove `0 O l 1 I`,
   which are easy to misread.
4. Click **Generate Password**:
   - Uses `secrets.choice()` / `secrets.randbelow()` throughout —
     never `random` — for cryptographic security.
   - Guarantees at least one character from every selected type.
   - Shows a colour-coded strength label (red = Weak, orange = Medium,
     green = Strong) based on length and character-type diversity.
   - Automatically copies the new password to your clipboard.
5. Use **Copy to Clipboard** any time to re-copy the current password.
6. The last 5 passwords generated in this session appear in the history
   list below — this list is **never written to disk**; it disappears
   the moment you close the app, by design, for security.

## Security notes

- The advanced tier never uses `random` for password characters —
  `random` is not cryptographically secure and is predictable if an
  attacker learns its internal state. `secrets` is designed for exactly
  this use case (tokens, passwords, security codes).
- Generated passwords are not saved to any file or database. Closing the
  app clears the on-screen history permanently.
- Clipboard copying uses `pyperclip`; if your OS/environment has no
  clipboard access (e.g. some headless Linux setups), copying will fail
  gracefully with an error message rather than crashing the app.

## Files

| File | Purpose |
|---|---|
| `beginner_password_generator.py` | CLI version (`random`) |
| `advanced_password_generator.py` | GUI version (`secrets`, strength meter, clipboard, history) |
