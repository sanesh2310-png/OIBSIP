"""
Advanced-Tier Voice Assistant
------------------------------
Includes every Beginner-tier feature (see beginner_assistant.py) plus:
  - Lightweight NLU: parses intent + entities from free-form sentences
    (uses nltk for tokenization/POS tagging; falls back to regex if
    nltk data isn't available, so the assistant still runs offline)
  - Send email via voice command (smtplib, use a dummy/test account)
  - Timed reminders that trigger an audible alert after N minutes
  - Live weather via OpenWeatherMap free tier
  - General knowledge Q&A via a local knowledge base (JSON), with an
    optional pluggable web QA API
  - Custom commands defined by the user in config.json (or added by voice)
  - Privacy notes: see README.md

Setup:
    pip install SpeechRecognition pyttsx3 pyaudio nltk requests

    First run only (downloads small NLTK models, ~10MB):
        python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

    Set environment variables (never hard-code secrets):
        OPENWEATHER_API_KEY   - from https://openweathermap.org/api
        EMAIL_ADDRESS         - sender address (use a dummy/test account)
        EMAIL_APP_PASSWORD    - app password / SMTP password
        SMTP_SERVER           - default smtp.gmail.com
        SMTP_PORT             - default 587

Run:
    python advanced_assistant.py
"""

import datetime
import json
import os
import re
import smtplib
import threading
import time
import webbrowser
from email.mime.text import MIMEText
from pathlib import Path

import requests
import speech_recognition as sr
import pyttsx3

try:
    import nltk
    from nltk import pos_tag, word_tokenize

    _NLTK_READY = True
except Exception:
    _NLTK_READY = False

CONFIG_PATH = Path(__file__).parent / "config.json"
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge_base.json"


# ---------------------------------------------------------------------------
# Configuration / persistence helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {path} is malformed, using defaults.")
    return default


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


DEFAULT_CONFIG = {
    "custom_commands": {
        # phrase user says -> canned response OR URL to open
        "open my notes": {"type": "url", "value": "https://keep.google.com"}
    },
    "weather_default_city": "London",
    "email_default_to": ""
}

DEFAULT_KNOWLEDGE_BASE = {
    "who created python": "Python was created by Guido van Rossum and first released in 1991.",
    "what is the speed of light": "The speed of light in a vacuum is about 299,792 kilometers per second.",
}


# ---------------------------------------------------------------------------
# Simple intent parser (rule-based NLU, no heavy ML dependency required)
# ---------------------------------------------------------------------------

class IntentParser:
    """
    Parses free-form spoken sentences into (intent, entities) instead of
    relying on rigid keyword matching. Uses POS tagging (if nltk data is
    available) to pull out entities like city names, search topics, and
    email recipients from natural phrasing such as:
        "hey can you tell me what the weather's like in Tokyo"
        "please send an email to sam about the meeting tomorrow"
        "set a reminder for 10 minutes to check the oven"
    """

    INTENT_PATTERNS = {
        "greet": [r"\bhello\b", r"\bhi\b", r"\bhey\b"],
        "time": [r"\btime\b"],
        "date": [r"\bdate\b", r"\btoday'?s date\b"],
        "search": [r"\bsearch (for|about)?\b", r"\blook up\b", r"\bgoogle\b"],
        "weather": [r"\bweather\b", r"\bforecast\b", r"\btemperature\b"],
        "email": [r"\bsend (an )?email\b", r"\bemail\b"],
        "reminder": [r"\bremind me\b", r"\bset a reminder\b", r"\btimer\b"],
        "question": [r"^\s*(who|what|when|where|why|how)\b"],
        "add_command": [r"\badd (a )?(custom )?command\b", r"\bteach you\b"],
        "exit": [r"\bexit\b", r"\bquit\b", r"\bstop\b", r"\bgoodbye\b"],
    }

    def parse(self, text: str):
        text = text.lower().strip()
        intent = self._match_intent(text)
        entities = self._extract_entities(intent, text)
        return intent, entities

    def _match_intent(self, text: str) -> str:
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return intent
        return "unknown"

    def _extract_entities(self, intent: str, text: str) -> dict:
        entities = {}

        if intent == "search":
            m = re.search(r"search (?:for|about)?\s*(.*)", text)
            entities["query"] = m.group(1).strip() if m else ""

        elif intent == "weather":
            # Look for "in <city>" or trailing proper-noun-ish tokens
            m = re.search(r"\bin\s+([a-zA-Z\s]+)$", text)
            if m:
                entities["city"] = m.group(1).strip()
            elif _NLTK_READY:
                entities["city"] = self._nltk_proper_noun_guess(text)

        elif intent == "email":
            to_match = re.search(r"\bto\s+([a-zA-Z0-9_.+-]+)", text)
            about_match = re.search(r"\babout\s+(.*)", text)
            entities["to"] = to_match.group(1) if to_match else ""
            entities["subject"] = about_match.group(1) if about_match else "Voice Assistant Message"

        elif intent == "reminder":
            time_match = re.search(r"(\d+)\s*(second|minute|hour)s?", text)
            about_match = re.search(r"\bto\s+(.*)", text)
            if time_match:
                entities["amount"] = int(time_match.group(1))
                entities["unit"] = time_match.group(2)
            entities["note"] = about_match.group(1) if about_match else "Reminder"

        elif intent == "question":
            entities["query"] = text

        elif intent == "add_command":
            # "add a command <phrase> that says <response>"
            m = re.search(r"command\s+(.*?)\s+that says\s+(.*)", text)
            if m:
                entities["phrase"] = m.group(1).strip()
                entities["response"] = m.group(2).strip()

        return entities

    @staticmethod
    def _nltk_proper_noun_guess(text: str) -> str:
        try:
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            proper_nouns = [w for w, tag in tagged if tag in ("NNP", "NNPS")]
            return " ".join(proper_nouns) if proper_nouns else ""
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# Voice Assistant
# ---------------------------------------------------------------------------

class AdvancedVoiceAssistant:
    def __init__(self, name="Jarvis"):
        self.name = name
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)

        self.parser = IntentParser()
        self.config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
        self.knowledge_base = load_json(KNOWLEDGE_BASE_PATH, DEFAULT_KNOWLEDGE_BASE)

        self.weather_api_key = os.environ.get("OPENWEATHER_API_KEY", "")
        self.email_address = os.environ.get("EMAIL_ADDRESS", "")
        self.email_password = os.environ.get("EMAIL_APP_PASSWORD", "")
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self._pending_add_command = False

    # ---------- Core I/O ----------

    def speak(self, text: str):
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, timeout=5, phrase_time_limit=10) -> str:
        with self.microphone as source:
            print("Listening...")
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                return ""
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't catch that. Could you please repeat?")
            return ""
        except sr.RequestError as e:
            self.speak("I'm having trouble reaching the speech recognition service.")
            print(f"Recognition service error: {e}")
            return ""

    # ---------- Feature implementations ----------

    def tell_time(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {now}.")

    def tell_date(self):
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.speak(f"Today's date is {today}.")

    def web_search(self, query: str):
        if not query:
            self.speak("What would you like me to search for?")
            return
        self.speak(f"Searching the web for {query}.")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def get_weather(self, city: str):
        city = city or self.config.get("weather_default_city", "London")
        if not self.weather_api_key:
            self.speak(
                "I don't have a weather API key configured. "
                "Set the OPENWEATHER_API_KEY environment variable to enable this."
            )
            return
        try:
            resp = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": self.weather_api_key, "units": "metric"},
                timeout=8,
            )
            data = resp.json()
            if resp.status_code != 200:
                self.speak(f"I couldn't find weather data for {city}.")
                return
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            self.speak(
                f"It's currently {temp:.0f} degrees Celsius in {city}, "
                f"feels like {feels_like:.0f}, with {desc}."
            )
        except requests.RequestException as e:
            self.speak("I couldn't reach the weather service right now.")
            print(f"Weather API error: {e}")

    def send_email(self, to: str, subject: str, body: str = None):
        if not self.email_address or not self.email_password:
            self.speak(
                "Email isn't configured. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD "
                "environment variables with a test account to enable this."
            )
            return
        recipient = to or self.config.get("email_default_to", "")
        if not recipient:
            self.speak("Who should I send the email to?")
            return
        if "@" not in recipient:
            self.speak(
                f"I only caught the name '{recipient}', not a full email address. "
                "Please configure a default recipient or provide the full address."
            )
            return

        body = body or f"This message was sent by {self.name}, your voice assistant."
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email_address
        msg["To"] = recipient

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, [recipient], msg.as_string())
            self.speak(f"Email sent to {recipient}.")
        except smtplib.SMTPException as e:
            self.speak("I ran into a problem sending that email.")
            print(f"SMTP error: {e}")

    def set_reminder(self, amount: int, unit: str, note: str):
        if not amount:
            self.speak("How long from now should I remind you?")
            return
        seconds = {"second": 1, "minute": 60, "hour": 3600}.get(unit, 60) * amount
        self.speak(f"Okay, I'll remind you to {note} in {amount} {unit}(s).")

        def alert():
            time.sleep(seconds)
            self.speak(f"Reminder: {note}")

        threading.Thread(target=alert, daemon=True).start()

    def answer_question(self, query: str):
        normalized = query.lower().strip().rstrip("?")
        if normalized in self.knowledge_base:
            self.speak(self.knowledge_base[normalized])
            return
        # Fuzzy fallback: partial match against stored questions
        for key, answer in self.knowledge_base.items():
            if key in normalized or normalized in key:
                self.speak(answer)
                return
        self.speak(
            "I don't have an answer for that in my knowledge base yet. "
            "You can add one by editing knowledge_base.json."
        )

    def add_custom_command(self, phrase: str, response: str):
        if not phrase or not response:
            self.speak(
                "To add a command, say something like: "
                "add a command 'good morning' that says 'rise and shine'."
            )
            return
        self.config.setdefault("custom_commands", {})[phrase] = {
            "type": "speak",
            "value": response,
        }
        save_json(CONFIG_PATH, self.config)
        self.speak(f"Got it. When you say '{phrase}', I'll respond with '{response}'.")

    def check_custom_commands(self, text: str) -> bool:
        text_lower = text.lower().strip()
        for phrase, action in self.config.get("custom_commands", {}).items():
            if phrase in text_lower:
                if action["type"] == "speak":
                    self.speak(action["value"])
                elif action["type"] == "url":
                    self.speak(f"Opening {phrase}.")
                    webbrowser.open(action["value"])
                return True
        return False

    # ---------- Dispatch ----------

    def handle_command(self, raw_text: str) -> bool:
        if not raw_text:
            return True

        # Custom commands take priority so users can override built-ins
        if self.check_custom_commands(raw_text):
            return True

        intent, entities = self.parser.parse(raw_text)

        if intent == "greet":
            self.speak("Hello! How can I help you today?")
        elif intent == "time":
            self.tell_time()
        elif intent == "date":
            self.tell_date()
        elif intent == "search":
            self.web_search(entities.get("query", ""))
        elif intent == "weather":
            self.get_weather(entities.get("city", ""))
        elif intent == "email":
            self.send_email(entities.get("to", ""), entities.get("subject", "Voice Assistant Message"))
        elif intent == "reminder":
            self.set_reminder(entities.get("amount"), entities.get("unit", "minute"), entities.get("note", "your reminder"))
        elif intent == "question":
            self.answer_question(entities.get("query", raw_text))
        elif intent == "add_command":
            self.add_custom_command(entities.get("phrase", ""), entities.get("response", ""))
        elif intent == "exit":
            self.speak("Goodbye! Have a great day.")
            return False
        else:
            self.speak(
                "I'm not sure how to help with that. "
                "You can ask about the time, date, weather, search the web, "
                "send an email, set a reminder, or ask a question."
            )

        return True

    # ---------- Main loop ----------

    def run(self):
        self.speak(
            f"{self.name} advanced mode is online. "
            "Ask me about the weather, set a reminder, send an email, or say 'exit' to quit."
        )
        running = True
        while running:
            text = self.listen()
            running = self.handle_command(text)


if __name__ == "__main__":
    assistant = AdvancedVoiceAssistant(name="Jarvis")
    assistant.run()
