"""
Advanced-Tier Chat Application — SERVER
------------------------------------------
Includes all Beginner-tier networking (socket + threading, real-time
bidirectional relay, graceful disconnect handling) plus:
  - User registration and login (username + password, stored in SQLite,
    passwords hashed with sha256 + per-user salt — never stored in plaintext)
  - Multiple named chat rooms — create or join by name
  - Message history stored in SQLite; the last 50 messages in a room are
    sent to a user when they join
  - Emoji shortcode rendering (e.g. :smile: -> 😄) applied server-side so
    all clients see the same rendered text
  - A simple line-based protocol (see PROTOCOL.md notes in README) so a
    plain socket client (or the provided tkinter GUI client) can talk to it

SECURITY NOTE (see README.md for the full write-up):
This is a learning/demo project. Traffic between client and server is
NOT encrypted (plain TCP, no TLS) — do not use this over an untrusted
network with real passwords. Passwords are hashed before storage, but
they are still sent from client to server in plaintext over the socket.

Run:
    python advanced_chat_server.py
"""

import hashlib
import os
import socket
import sqlite3
import threading
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5556
DB_PATH = "chat_app.db"

EMOJI_MAP = {
    ":smile:": "😄", ":laugh:": "😂", ":heart:": "❤️", ":thumbsup:": "👍",
    ":sad:": "😢", ":wink:": "😉", ":thinking:": "🤔", ":fire:": "🔥",
    ":party:": "🎉", ":wave:": "👋", ":ok:": "👌", ":clap:": "👏",
}

db_lock = threading.Lock()
rooms_lock = threading.Lock()
# room_name -> list of (conn, username)
active_rooms = {}


def timestamp() -> str:
    return datetime.now().strftime("%H:%M")


def render_emoji(text: str) -> str:
    for code, symbol in EMOJI_MAP.items():
        text = text.replace(code, symbol)
    return text


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                sent_at TEXT NOT NULL
            )
        """)


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def register_user(username: str, password: str) -> (bool, str):
    salt = os.urandom(16).hex()
    pw_hash = hash_password(password, salt)
    try:
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt, pw_hash),
            )
        return True, "Registered successfully."
    except sqlite3.IntegrityError:
        return False, "That username is already taken."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def authenticate_user(username: str, password: str) -> (bool, str):
    try:
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            return False, "No such user. Please register first."
        salt, stored_hash = row
        if hash_password(password, salt) == stored_hash:
            return True, "Login successful."
        return False, "Incorrect password."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def save_message(room: str, username: str, content: str):
    try:
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO messages (room, username, content, sent_at) VALUES (?, ?, ?, ?)",
                (room, username, content, datetime.now().isoformat()),
            )
    except sqlite3.Error as e:
        print(f"Warning: could not save message to history: {e}")


def get_recent_history(room: str, limit: int = 50):
    try:
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                """SELECT username, content, sent_at FROM messages
                   WHERE room = ? ORDER BY id DESC LIMIT ?""",
                (room, limit),
            ).fetchall()
        return list(reversed(rows))
    except sqlite3.Error as e:
        print(f"Warning: could not read message history: {e}")
        return []


# ---------------------------------------------------------------------------
# Room / broadcast helpers
# ---------------------------------------------------------------------------

def join_room(room: str, conn, username: str):
    with rooms_lock:
        active_rooms.setdefault(room, []).append((conn, username))


def leave_room(room: str, conn):
    with rooms_lock:
        if room in active_rooms:
            active_rooms[room] = [(c, u) for c, u in active_rooms[room] if c is not conn]


def broadcast_to_room(room: str, message: str, exclude_conn=None):
    with rooms_lock:
        members = list(active_rooms.get(room, []))
    for conn, _username in members:
        if conn is exclude_conn:
            continue
        try:
            conn.sendall(message.encode("utf-8"))
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Client handling
# ---------------------------------------------------------------------------

def send_line(conn, text: str):
    try:
        conn.sendall((text + "\n").encode("utf-8"))
    except OSError:
        pass


def handle_client(conn: socket.socket, addr):
    username = None
    room = None
    try:
        send_line(conn, "AUTH_REQUIRED Please REGISTER <user> <pass> or LOGIN <user> <pass>")

        # --- Authentication loop ---
        while True:
            raw = conn.recv(1024).decode("utf-8").strip()
            if not raw:
                return
            parts = raw.split(" ", 2)
            command = parts[0].upper()

            if command == "REGISTER" and len(parts) == 3:
                ok, msg = register_user(parts[1], parts[2])
                send_line(conn, f"{'OK' if ok else 'ERROR'} {msg}")
                if ok:
                    username = parts[1]
                    break
            elif command == "LOGIN" and len(parts) == 3:
                ok, msg = authenticate_user(parts[1], parts[2])
                send_line(conn, f"{'OK' if ok else 'ERROR'} {msg}")
                if ok:
                    username = parts[1]
                    break
            else:
                send_line(conn, "ERROR Unrecognized command. Use REGISTER or LOGIN.")

        # --- Room selection ---
        send_line(conn, "ROOM_REQUIRED Send: JOIN <room_name>")
        while True:
            raw = conn.recv(1024).decode("utf-8").strip()
            parts = raw.split(" ", 1)
            if parts[0].upper() == "JOIN" and len(parts) == 2:
                room = parts[1].strip()
                break
            send_line(conn, "ERROR Send: JOIN <room_name>")

        join_room(room, conn, username)
        print(f"[{timestamp()}] {username} joined room '{room}' from {addr}.")

        # Send recent history for this room
        history = get_recent_history(room)
        for hist_user, hist_content, hist_time in history:
            hh_mm = datetime.fromisoformat(hist_time).strftime("%H:%M")
            send_line(conn, f"[{hh_mm}] {hist_user}: {hist_content}")

        send_line(conn, f"JOINED {room}")
        broadcast_to_room(room, f"[{timestamp()}] SERVER: {username} has joined {room}.", exclude_conn=conn)

        # --- Main chat loop ---
        while True:
            data = conn.recv(2048)
            if not data:
                break
            text = data.decode("utf-8").strip()
            if not text:
                continue
            rendered = render_emoji(text)
            save_message(room, username, rendered)
            line = f"[{timestamp()}] {username}: {rendered}"
            print(line)
            broadcast_to_room(room, line, exclude_conn=conn)

    except (ConnectionResetError, ConnectionAbortedError):
        pass
    finally:
        if room:
            leave_room(room, conn)
            display_name = username or "A user"
            broadcast_to_room(room, f"[{timestamp()}] SERVER: {display_name} has left {room}.")
            print(f"[{timestamp()}] {display_name} disconnected from '{room}'.")
        conn.close()


def main():
    init_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Advanced chat server listening on port {PORT}. Waiting for clients...")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
