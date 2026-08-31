# Chat Application

A real-time chat app with two tiers:

- **Beginner** (`chat_server.py` + `chat_client.py`) — a two-user
  command-line chat over raw sockets, with threading for simultaneous
  send/receive.
- **Advanced** (`advanced_chat_server.py` + `advanced_chat_client.py`) —
  a full GUI app with login/registration, multiple rooms, persistent
  message history, emoji shortcodes, and unfocused-window notifications.

## Beginner Tier

**Run the server first**, in one terminal:
```bash
python chat_server.py
```
It listens on `localhost:5555` and waits for up to 2 clients.

**Then run the client**, in two separate terminals (simulating two users
on the same machine):
```bash
python chat_client.py
```
Each will ask for a name, then let you type messages. Messages you send
appear on the other client prefixed with a timestamp, e.g.:
```
[14:35] Alice: Hello
```
Type `exit` to disconnect — the other client is notified automatically.

To chat across two different computers instead of one machine, change
`HOST` in `chat_client.py` to the server machine's IP address (and make
sure port 5555 is reachable between them).

## Advanced Tier

**Install the optional dependency** (enables real desktop notifications;
the app still works without it):
```bash
pip install plyer
```

**Run the server:**
```bash
python advanced_chat_server.py
```
This creates `chat_app.db` (SQLite) on first run, listens on
`localhost:5556`, and can handle many simultaneous clients across
multiple rooms.

**Run the client** (once per user):
```bash
python advanced_chat_client.py
```

**How it works:**
1. **Login/Register** — enter a username and password. Registering
   creates a new account; logging in checks against the stored hash.
2. **Join a room** — type any room name. If it doesn't exist yet, it's
   created automatically the moment someone joins it.
3. **Chat** — the last 50 messages in that room are loaded automatically
   so you can see the conversation so far.
4. **Emoji shortcodes** — typing `:smile:`, `:fire:`, `:heart:`,
   `:wave:`, `:thumbsup:`, `:laugh:`, `:sad:`, `:wink:`, `:thinking:`,
   `:party:`, `:ok:`, or `:clap:` renders as the matching emoji for
   everyone in the room (rendering happens on the server, so it's
   consistent for all clients).
5. **Notifications** — if the chat window loses focus (you switch to
   another app) and a new message arrives, you'll get an OS desktop
   notification (via `plyer`) or, if `plyer` isn't installed, the window
   title flashes "New message!" until you click back into the window.

## Security & Privacy — what's stored, what's not encrypted

This is a learning/demo project, not a production-secure messenger.
Please read this before using it for anything beyond practice:

**What is stored, and how:**
- Usernames and passwords are stored in a local SQLite database
  (`chat_app.db`). Passwords are **never stored in plaintext** — each
  password is combined with a random per-user salt and hashed with
  SHA-256 before being saved. The server cannot recover your original
  password from what's stored.
- Chat messages are stored in the same SQLite database (table
  `messages`), in **plaintext**, tagged with room, sender, and
  timestamp, so message history can be replayed when someone joins a
  room. There is no message deletion/expiry built in — history persists
  indefinitely on the server's disk.

**What is NOT encrypted (important):**
- All network traffic between client and server — including your
  password during login/registration, and every chat message — travels
  over a **plain, unencrypted TCP socket**. There is no TLS/SSL layer.
  Anyone able to observe network traffic between a client and the
  server (e.g. on a shared or untrusted network) could read passwords
  and messages in transit.
- This is why the app is intended for `localhost` use or trusted
  private networks (e.g. a local LAN for a class project) — **do not**
  run this over the public internet with real credentials or sensitive
  conversations.
- If you want to harden this for real use, the standard next steps
  would be: wrap the sockets in TLS (`ssl` module), and consider a
  stronger password hashing scheme (e.g. `bcrypt`/`argon2` instead of
  raw SHA-256) with per-deployment configuration rather than a fixed
  scheme.

## Files

| File | Purpose |
|---|---|
| `chat_server.py` | Beginner CLI server (2-user relay) |
| `chat_client.py` | Beginner CLI client |
| `advanced_chat_server.py` | Advanced server: auth, rooms, history, emoji rendering |
| `advanced_chat_client.py` | Advanced GUI client (tkinter) |
| `chat_app.db` | Auto-created by the advanced server on first run (not included) |
