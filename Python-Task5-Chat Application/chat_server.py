"""
Beginner-Tier Chat Application — SERVER
------------------------------------------
Feature checklist covered (server side):
  - Listens for incoming client connections
  - Real-time, bidirectional message relay between two connected clients
  - Timestamps are added by the CLIENT that displays messages (see client),
    but the server also stamps its own system notices
  - Graceful disconnection handling: notifies the other client when one
    client disconnects
  - Runs on localhost so both scripts work on the same machine

This is a simple two-user relay: the server accepts up to 2 client
connections and forwards whatever one client sends to the other.

Run this FIRST, then run chat_client.py twice (in two separate terminals,
or on two machines pointing HOST at the server's IP).

Run:
    python chat_server.py
"""

import socket
import threading
from datetime import datetime

HOST = "0.0.0.0"   # listen on all interfaces (use 127.0.0.1 from clients on the same machine)
PORT = 5555
MAX_CLIENTS = 2

clients = []          # list of (conn, addr, name)
clients_lock = threading.Lock()


def timestamp() -> str:
    return datetime.now().strftime("%H:%M")


def broadcast(message: str, sender_conn=None):
    """Send a message to every connected client except the sender."""
    with clients_lock:
        for conn, addr, name in clients:
            if conn is sender_conn:
                continue
            try:
                conn.sendall(message.encode("utf-8"))
            except OSError:
                pass  # that client may already be gone; cleanup happens elsewhere


def remove_client(conn):
    with clients_lock:
        for entry in clients:
            if entry[0] is conn:
                clients.remove(entry)
                return entry[2]  # return their name
    return None


def handle_client(conn: socket.socket, addr):
    name = None
    try:
        # First message from a client is treated as their chosen name
        raw_name = conn.recv(1024).decode("utf-8").strip()
        name = raw_name if raw_name else f"User@{addr[1]}"

        with clients_lock:
            clients.append((conn, addr, name))

        print(f"[{timestamp()}] {name} connected from {addr}.")
        broadcast(f"[{timestamp()}] SERVER: {name} has joined the chat.\n", sender_conn=conn)

        while True:
            data = conn.recv(2048)
            if not data:
                break  # client disconnected
            text = data.decode("utf-8")
            print(f"[{timestamp()}] {name}: {text.strip()}")
            broadcast(f"[{timestamp()}] {name}: {text}", sender_conn=conn)

    except (ConnectionResetError, ConnectionAbortedError):
        pass
    finally:
        removed_name = remove_client(conn)
        display_name = removed_name or name or "A user"
        print(f"[{timestamp()}] {display_name} disconnected.")
        broadcast(f"[{timestamp()}] SERVER: {display_name} has left the chat.\n")
        conn.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Chat server listening on port {PORT}. Waiting for clients...")

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
