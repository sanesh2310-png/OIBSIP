"""
Advanced-Tier Chat Application — GUI CLIENT (tkinter)
--------------------------------------------------------
Talks to advanced_chat_server.py using the simple line-based protocol:
    Auth:   REGISTER <user> <pass>  /  LOGIN <user> <pass>
    Room:   JOIN <room_name>
    Chat:   any other line is treated as a message to the joined room

Features covered:
  - GUI chat window (tkinter) — login/register screen, then chat screen
  - Multiple chat rooms: type any room name to create or join it
  - Message history: shown automatically when you join a room
    (rendered by the server, this client just displays it)
  - Desktop notification when a message arrives and the window is not
    focused (uses the OS's `plyer` if available; otherwise falls back to
    flashing the window title, which needs no extra dependency)
  - Emoji shortcodes are rendered server-side, so any client (even a
    plain socket client) sees the same emoji

Install:
    pip install plyer   # optional — enables real desktop notifications
                         # the app still works without it (title-flash fallback)

Run the server first (advanced_chat_server.py), then:
    python advanced_chat_client.py
"""

import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

try:
    from plyer import notification
    _HAS_PLYER = True
except Exception:
    _HAS_PLYER = False

HOST = "127.0.0.1"
PORT = 5556


class ChatClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chat Application - Login")
        self.geometry("420x480")
        self.configure(bg="#f8fafc")

        self.sock = None
        self.username = None
        self.room = None
        self.window_focused = True
        self._flash_job = None

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        self._build_auth_screen()

    # ---- Focus tracking (for the "not focused" notification requirement) ----

    def _on_focus_in(self, event):
        self.window_focused = True
        if self._flash_job:
            self.after_cancel(self._flash_job)
            self._flash_job = None
        self.title(f"Chat - {self.room}" if self.room else "Chat Application")

    def _on_focus_out(self, event):
        self.window_focused = False

    def _notify_new_message(self, sender: str, text: str):
        if self.window_focused:
            return  # only notify when the window isn't focused

        if _HAS_PLYER:
            try:
                notification.notify(title=f"New message from {sender}", message=text, timeout=4)
                return
            except Exception:
                pass  # fall through to title-flash fallback

        # Fallback: flash the window title so it's visible in the taskbar
        self._flash_title()

    def _flash_title(self):
        current = self.title()
        new_title = "New message!" if current != "New message!" else f"Chat - {self.room}"
        self.title(new_title)
        self._flash_job = self.after(800, self._flash_title)

    # ---- Screen 1: Login / Register ----

    def _build_auth_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Chat Application", font=("Segoe UI", 18, "bold"), bg="#f8fafc").pack(pady=(30, 20))

        form = tk.Frame(self, bg="#f8fafc")
        form.pack()

        tk.Label(form, text="Username:", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.username_entry = tk.Entry(form, font=("Segoe UI", 11))
        self.username_entry.grid(row=0, column=1, padx=8, pady=8)

        tk.Label(form, text="Password:", bg="#f8fafc", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.password_entry = tk.Entry(form, font=("Segoe UI", 11), show="*")
        self.password_entry.grid(row=1, column=1, padx=8, pady=8)

        btn_frame = tk.Frame(self, bg="#f8fafc")
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text="Login", width=12, bg="#2563eb", fg="white", bd=0,
                  command=lambda: self._connect_and_auth("LOGIN")).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Register", width=12, bg="#16a34a", fg="white", bd=0,
                  command=lambda: self._connect_and_auth("REGISTER")).grid(row=0, column=1, padx=6)

        self.auth_status_label = tk.Label(self, text="", bg="#f8fafc", fg="#dc2626", font=("Segoe UI", 10))
        self.auth_status_label.pack(pady=6)

    def _connect_and_auth(self, mode: str):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.auth_status_label.configure(text="Please enter both a username and password.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((HOST, PORT))
            self.sock.recv(1024)  # AUTH_REQUIRED banner, ignore text
            self.sock.sendall(f"{mode} {username} {password}".encode("utf-8"))
            response = self.sock.recv(1024).decode("utf-8").strip()
        except (ConnectionRefusedError, socket.timeout) as e:
            messagebox.showerror("Connection Error", f"Could not reach the chat server:\n{e}")
            return

        if response.startswith("OK"):
            self.username = username
            self.sock.recv(1024)  # ROOM_REQUIRED banner
            self._build_room_screen()
        else:
            self.auth_status_label.configure(text=response.replace("ERROR ", ""))
            self.sock.close()
            self.sock = None

    # ---- Screen 2: Room picker ----

    def _build_room_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text=f"Welcome, {self.username}!", font=("Segoe UI", 15, "bold"), bg="#f8fafc").pack(pady=(30, 10))
        tk.Label(self, text="Enter a room name to create or join it:", bg="#f8fafc", font=("Segoe UI", 11)).pack(pady=(0, 10))

        self.room_entry = tk.Entry(self, font=("Segoe UI", 11), justify="center")
        self.room_entry.pack(pady=6)
        self.room_entry.insert(0, "general")

        tk.Button(self, text="Join Room", bg="#2563eb", fg="white", bd=0, width=16,
                  command=self._join_room).pack(pady=16)

    def _join_room(self):
        room = self.room_entry.get().strip()
        if not room:
            messagebox.showwarning("Missing Room", "Please enter a room name.")
            return
        self.room = room
        self.sock.sendall(f"JOIN {room}".encode("utf-8"))
        self._build_chat_screen()

        receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        receiver_thread.start()

    # ---- Screen 3: Chat window ----

    def _build_chat_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.title(f"Chat - {self.room}")

        self.chat_display = scrolledtext.ScrolledText(self, state="disabled", wrap="word", font=("Segoe UI", 10))
        self.chat_display.pack(fill="both", expand=True, padx=8, pady=8)

        entry_frame = tk.Frame(self, bg="#f8fafc")
        entry_frame.pack(fill="x", padx=8, pady=(0, 8))

        self.message_entry = tk.Entry(entry_frame, font=("Segoe UI", 11))
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.message_entry.bind("<Return>", lambda event: self._send_message())

        tk.Button(entry_frame, text="Send", bg="#2563eb", fg="white", bd=0,
                  command=self._send_message).pack(side="right")

        hint = tk.Label(self, text="Tip: try emoji shortcodes like :smile: :fire: :heart: :wave:",
                         font=("Segoe UI", 8), bg="#f8fafc", fg="#6b7280")
        hint.pack(pady=(0, 6))

    def _append_chat_line(self, line: str):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", line + "\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        try:
            self.sock.sendall((text + "\n").encode("utf-8"))
        except OSError:
            messagebox.showerror("Connection Error", "Message could not be sent.")
            return
        self.message_entry.delete(0, "end")

    def _receive_loop(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(2048)
            except OSError:
                break
            if not data:
                self._append_chat_line("[Connection closed by server.]")
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    self.after(0, self._append_chat_line, line)
                    sender = line.split(":", 1)[0] if ":" in line else "Server"
                    self.after(0, self._notify_new_message, sender, line)


if __name__ == "__main__":
    app = ChatClientApp()
    app.mainloop()
