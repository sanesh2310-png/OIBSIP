"""
Beginner-Tier Random Password Generator (Command Line)
--------------------------------------------------------
Feature checklist covered:
  - Prompt for password length (minimum 8 enforced)
  - Prompt for character types to include: uppercase, lowercase,
    numbers, symbols (at least 2 types must be selected)
  - Generate and display a password matching the chosen criteria
  - Input validation: reject invalid lengths or too few character types
  - Option to generate another password without restarting

Run:
    python beginner_password_generator.py
"""

import random
import string


def get_length() -> int:
    """Ask for a password length, enforcing a minimum of 8."""
    while True:
        raw = input("Enter desired password length (minimum 8): ").strip()
        try:
            length = int(raw)
        except ValueError:
            print("  ⚠ Please enter a whole number (e.g. 12).")
            continue

        if length < 8:
            print("  ⚠ Length must be at least 8 characters for a safe password.")
            continue

        return length


def get_character_types() -> dict:
    """
    Ask which character types to include. At least 2 must be chosen.
    Returns a dict of type -> bool.
    """
    print("\nWhich character types should the password include?")
    print("(Answer y/n for each. At least 2 types must be chosen.)")

    while True:
        choices = {
            "uppercase": input("  Include uppercase letters (A-Z)? (y/n): ").strip().lower() == "y",
            "lowercase": input("  Include lowercase letters (a-z)? (y/n): ").strip().lower() == "y",
            "numbers": input("  Include numbers (0-9)? (y/n): ").strip().lower() == "y",
            "symbols": input("  Include symbols (!@#$...)? (y/n): ").strip().lower() == "y",
        }

        selected_count = sum(choices.values())
        if selected_count < 2:
            print("  ⚠ Please select at least 2 character types.\n")
            continue

        return choices


def build_character_pool(choices: dict) -> str:
    pool = ""
    if choices["uppercase"]:
        pool += string.ascii_uppercase
    if choices["lowercase"]:
        pool += string.ascii_lowercase
    if choices["numbers"]:
        pool += string.digits
    if choices["symbols"]:
        pool += string.punctuation
    return pool


def generate_password(length: int, choices: dict) -> str:
    pool = build_character_pool(choices)
    return "".join(random.choice(pool) for _ in range(length))


def main():
    print("=" * 50)
    print("       RANDOM PASSWORD GENERATOR (CLI)")
    print("=" * 50)

    while True:
        length = get_length()
        choices = get_character_types()
        password = generate_password(length, choices)

        print("-" * 50)
        print(f"Generated password: {password}")
        print("-" * 50)

        again = input("\nGenerate another password? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye! Stay secure. 🔒")
            break
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExited. Goodbye!")
