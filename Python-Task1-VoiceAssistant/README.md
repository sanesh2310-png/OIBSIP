# Python Voice Assistant

A voice-controlled assistant with two tiers:

- **`beginner_assistant.py`** — mic capture, greeting, time/date, web search,
  error handling, text-to-speech.
- **`advanced_assistant.py`** — everything above, plus lightweight NLU intent
  parsing, email sending, timed reminders, live weather, a local Q&A
  knowledge base, and user-defined custom commands.

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

**PyAudio** (the microphone backend) needs a system library first:

| OS      | Command |
|---------|---------|
| Windows | `pip install pyaudio` usually works directly |
| macOS   | `brew install portaudio && pip install pyaudio` |
| Linux   | `sudo apt-get install portaudio19-dev && pip install pyaudio` |

**NLTK data** (advanced tier only, first run):

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

If this data isn't downloaded, the advanced assistant still runs — entity
extraction falls back to regex-only parsing instead of POS tagging.

## 2. Configure secrets (advanced tier)

Never hard-code credentials. Set environment variables instead:

```bash
export OPENWEATHER_API_KEY="your_key_from_openweathermap.org"
export EMAIL_ADDRESS="your_test_account@gmail.com"
export EMAIL_APP_PASSWORD="your_app_password"   # not your normal password
export SMTP_SERVER="smtp.gmail.com"             # default shown
export SMTP_PORT="587"                          # default shown
```

- Get a free OpenWeatherMap key at https://openweathermap.org/api.
- For Gmail, create an **app password** (Google Account → Security → App
  Passwords) rather than using your real login password, and use a
  dummy/test account for development.
- Any missing credential simply disables that one feature — the assistant
  tells you it's not configured rather than crashing.

## 3. Run it

```bash
python beginner_assistant.py
# or
python advanced_assistant.py
```

Say things like:
- "Hello"
- "What time is it?"
- "What's today's date?"
- "Search for python tutorials"
- "What's the weather in Tokyo?"
- "Send an email to sam@example.com about the meeting"
- "Set a reminder for 5 minutes to check the oven"
- "Who created Python?"
- "Add a command 'good morning' that says 'rise and shine'"
- "Exit"

## 4. Customize

- **`config.json`** — add custom voice-triggered commands (either a canned
  spoken response or a URL to open) without touching code. You can also add
  commands by voice at runtime; they're saved back to this file.
- **`knowledge_base.json`** — add your own question/answer pairs for the
  general-knowledge feature.

## Privacy — what data is processed, and how

This is a local application; here's exactly what leaves your machine and why:

| Data | Where it goes | Why |
|---|---|---|
| Microphone audio | Google's speech-recognition web API (via the `speech_recognition` library's default recognizer) | Converts your spoken audio to text. Audio is sent per-utterance and is not stored by this app. |
| Search queries | Your default web browser → Google search | Opens a normal browser search; handled by your browser like any manual search. |
| City name (weather requests) | OpenWeatherMap API | Needed to look up current conditions for that city. No other personal data is sent. |
| Email address, subject, and message body (email feature) | Your configured SMTP server (e.g., Gmail) | Required to actually send the email you asked for. Use a dummy/test account while developing. |
| Custom commands and knowledge-base entries | Saved locally only, in `config.json` / `knowledge_base.json` on your machine | Never transmitted anywhere; purely local persistence. |
| Reminders | Kept in memory only, for the life of the running process | Not persisted or transmitted. |

**Recommendations if you extend this project:**
- Don't commit `config.json` if you add real personal defaults (default
  recipient email, home city) to version control.
- Never hard-code API keys or passwords in source files — this project
  reads them from environment variables for that reason.
- If you swap in a different speech-recognition backend, check whether it
  processes audio locally (more private) or sends it to a cloud API (like
  the default Google recognizer here) and document that trade-off for
  your users.
