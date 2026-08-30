# BMI Calculator

A Body Mass Index calculator with two tiers:

- **`beginner_bmi.py`** — command-line tool. Prompts for weight/height,
  calculates BMI, classifies it, and validates input.
- **`advanced_bmi.py`** — full GUI app (tkinter) with colour-coded results,
  multi-user history stored in SQLite, and a matplotlib BMI trend graph.

## Beginner Tier

**Run:**
```bash
python beginner_bmi.py
```

No dependencies beyond the Python standard library. You'll be prompted for
weight (kg) and height (m); non-numeric or non-positive input is rejected
with a message, and you're asked again. Output shows BMI rounded to 2
decimal places plus the category:

| Category     | BMI range      |
|---|---|
| Underweight  | < 18.5          |
| Normal       | 18.5 – 24.9     |
| Overweight   | 25.0 – 29.9     |
| Obese        | ≥ 30.0          |

## Advanced Tier

**Install dependencies:**
```bash
pip install matplotlib
```
`tkinter` and `sqlite3` ship with standard Python. On some Linux distros,
tkinter needs a separate system package:
```bash
sudo apt-get install python3-tk
```

**Run:**
```bash
python advanced_bmi.py
```

**How it works:**
1. Enter a name, weight (kg), and height (m), then click **Calculate**.
2. The result panel changes colour based on category (blue = underweight,
   green = normal, orange = overweight, red = obese).
3. Every calculation is saved to a local SQLite database
   (`bmi_records.db`, created automatically on first run) under the name
   you entered — enter the same name again later to keep building history
   for that person.
4. Click **View BMI Trend Graph** to open a matplotlib line chart of that
   user's BMI over time, with the healthy range (18.5–25) shaded.
5. Database errors (e.g. file permission issues) show a message box
   instead of crashing the app.

**Data storage:** all records stay in `bmi_records.db` on your local
machine — nothing is sent anywhere over the network.

## Files

| File | Purpose |
|---|---|
| `beginner_bmi.py` | CLI version |
| `advanced_bmi.py` | GUI version with persistence + graphing |
| `bmi_records.db` | Auto-created by the GUI app on first run (not included) |
