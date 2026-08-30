"""
Beginner-Tier Voice Assistant
------------------------------
Feature checklist covered:
  - Capture voice input via microphone (speech_recognition)
  - Respond to "Hello" with a predefined greeting
  - Tell the current time and date on request
  - Perform a web search on a user-specified topic (opens browser)
  - Graceful error handling: ask the user to repeat if unclear
  - Text-to-speech feedback for all responses (pyttsx3)

Setup:
    pip install SpeechRecognition pyttsx3 pyaudio
    (Windows: pip install pyaudio  |  macOS: brew install portaudio && pip install pyaudio
     Linux:   sudo apt-get install python3-pyaudio  OR  sudo apt-get install portaudio19-dev)

Run:
    python beginner_assistant.py
"""

import datetime
import webbrowser

import speech_recognition as sr
import pyttsx3


class VoiceAssistant:
    def __init__(self, name="Assistant"):
        self.name = name
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Text-to-speech engine setup
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

        # Calibrate for ambient noise once at startup
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    # ---------- Core I/O ----------

    def speak(self, text: str):
        """Speak text aloud and print it for visibility/debugging."""
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, timeout=5, phrase_time_limit=8) -> str:
        """
        Capture audio from the microphone and return recognized text
        (lowercased). Returns an empty string if nothing was understood,
        so callers can decide how to react.
        """
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
            return text.lower()
        except sr.UnknownValueError:
            # Graceful error handling — speech was not understood
            self.speak("Sorry, I didn't catch that. Could you please repeat?")
            return ""
        except sr.RequestError as e:
            self.speak("I'm having trouble reaching the speech recognition service.")
            print(f"Recognition service error: {e}")
            return ""

    # ---------- Command handling ----------

    def handle_command(self, command: str) -> bool:
        """
        Route a recognized command to the right feature.
        Returns False if the assistant should stop running.
        """
        if not command:
            return True

        if "hello" in command or "hi " in command or command.strip() == "hi":
            self.speak("Hello! How can I help you today?")

        elif "time" in command:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {now}.")

        elif "date" in command:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speak(f"Today's date is {today}.")

        elif "search for" in command or "search" in command:
            query = self._extract_after(command, ["search for", "search"])
            if query:
                self.speak(f"Searching the web for {query}.")
                webbrowser.open(f"https://www.google.com/search?q={query}")
            else:
                self.speak("What would you like me to search for?")

        elif any(word in command for word in ["exit", "quit", "stop", "goodbye"]):
            self.speak("Goodbye! Have a great day.")
            return False

        else:
            self.speak(
                "I'm not sure how to help with that yet. "
                "Try asking for the time, the date, or to search for something."
            )

        return True

    @staticmethod
    def _extract_after(command: str, triggers) -> str:
        """Return whatever text follows the first matching trigger phrase."""
        for trigger in sorted(triggers, key=len, reverse=True):
            if trigger in command:
                return command.split(trigger, 1)[1].strip()
        return ""

    # ---------- Main loop ----------

    def run(self):
        self.speak(f"{self.name} is online. Say 'hello' to get started, or 'exit' to quit.")
        running = True
        while running:
            command = self.listen()
            running = self.handle_command(command)


if __name__ == "__main__":
    assistant = VoiceAssistant(name="Jarvis")
    assistant.run()
