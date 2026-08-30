"""
Beginner-Tier BMI Calculator (Command Line)
--------------------------------------------
Feature checklist covered:
  - Prompt user for weight (kg) and height (m) via command line
  - Calculate BMI = weight / (height ** 2)
  - Classify into Underweight / Normal / Overweight / Obese
  - Display BMI rounded to 2 decimal places, plus category
  - Input validation: reject non-numeric and negative/zero values,
    with a helpful error message, and let the user try again

Run:
    python beginner_bmi.py
"""


def get_positive_float(prompt: str) -> float:
    """
    Keep asking until the user enters a valid positive number.
    Rejects non-numeric input and zero/negative values.
    """
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("  ⚠ That doesn't look like a number. Please enter digits only (e.g. 70 or 1.75).")
            continue

        if value <= 0:
            print("  ⚠ Please enter a positive number greater than zero.")
            continue

        return value


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """BMI = weight (kg) / height (m) squared."""
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi: float) -> str:
    """Map a BMI value to the standard WHO category."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def main():
    print("=" * 45)
    print("        BMI CALCULATOR (Command Line)")
    print("=" * 45)

    weight = get_positive_float("Enter your weight in kilograms (kg): ")
    height = get_positive_float("Enter your height in meters (m), e.g. 1.75: ")

    bmi = calculate_bmi(weight, height)
    category = classify_bmi(bmi)

    print("-" * 45)
    print(f"Your BMI is: {bmi:.2f}")
    print(f"Category:    {category}")
    print("-" * 45)

    print("\nReference ranges:")
    print("  Underweight : below 18.5")
    print("  Normal      : 18.5 - 24.9")
    print("  Overweight  : 25.0 - 29.9")
    print("  Obese       : 30.0 and above")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExited. Goodbye!")
