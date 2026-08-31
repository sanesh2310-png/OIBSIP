"""
Beginner-Tier Chat Application — CLIENT
------------------------------------------
Feature checklist covered (client side):
  - Connects to the server
  - Real-time, bidirectional message exchange (send in main thread,
    receive in a background thread so both happen simultaneously)
  - Messages displayed with a timestamp prefix (e.g., "[14:35] Alice: Hello")
    — the server sends messages already stamped; this client also stamps
    its own outgoing echo for consistency
  - Graceful disconnection handling: shows a notice when the other user
    (or the server) disconnects, instead of crashing
  - Connects via localhost by default so two instances can run on one machine

Run the server FIRST (chat_server.py), then run this script — once per
user, in separate terminals.

Run:
    python chat_client.py
"""

import socket
import threading
from datetime import datetime

HOST = "127.0.0.1"   # change to the server's IP if connecting across machines
PORT = 5555


def timestamp() -> str:
    return datetime.now().strftime("%H:%M")


def receive_messages(sock: socket.socket):
    """Background thread: continuously print whatever the server sends."""
    while True:
        try:
            data = sock.recv(2048)
        except OSError:
            break
        if not data:
            print("\n[Connection closed by server.]")
            break
        print(data.decode("utf-8"), end="")
    print("You can no longer send messages. Press Enter to exit.")


def main():
    name = input("Enter your name: ").strip() or "Anonymous"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT}. Is chat_server.py running?")
        return

    sock.sendall(name.encode("utf-8"))

    receiver_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver_thread.start()

    print(f"Connected as {name}. Type a message and press Enter to send. Type 'exit' to quit.\n")

    try:
        while True:
            message = input()
            if message.strip().lower() == "exit":
                break
            if message.strip() == "":
                continue
            try:
                sock.sendall((message + "\n").encode("utf-8"))
                print(f"[{timestamp()}] You: {message}")
            except OSError:
                print("Message could not be sent — connection may be closed.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print("Disconnected. Goodbye!")


if __name__ == "__main__":
    main()
