import base64
import os

# Google Desktop OAuth uses a loopback callback on 127.0.0.1.
# OAuthLib normally rejects HTTP loopback URLs before the callback is handled.
# This setting is intentionally limited to this local-only application.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
import random
import re
import threading
import time
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

app = Flask(__name__)
UI_HOST = "127.0.0.1"
AUTH_HOST = "127.0.0.1"
UI_PORT = None
AUTH_PORT = None

state = {
    "creds": None,
    "email": None,
    "authenticated": False,
    "auth_url": None,
    "auth_error": None,
    # Keep the exact OAuth Flow object that generated the authorization URL.
    # This preserves its PKCE code_verifier and OAuth state until the callback.
    "oauth_flow": None,
    "job": {
        "running": False,
        "requested": 0,
        "created": 0,
        "failed": 0,
        "current_subject": "",
        "error": "",
        "done": False,
        "stop_requested": False,
    },
}
lock = threading.Lock()


def find_free_port():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def ask_port(label, default_text):
    while True:
        raw = input(f"{label} [{default_text}]: ").strip()

        # Empty input means: automatically select a free localhost port.
        if raw == "":
            return find_free_port()

        try:
            port = int(raw)
            if 1 <= port <= 65535:
                return port
            print("Port must be between 1 and 65535.")
        except ValueError:
            print("Please enter a valid port number or press Enter for automatic selection.")


def choose_ports():
    print()
    print("=" * 68)
    print(" Gmail Bulk Draft Builder - Port Configuration")
    print("=" * 68)
    print("Both services always bind to 127.0.0.1.")
    print()
    print("You have two ways to use the app:")
    print()
    print("  LOCAL / iSH")
    print("    Press Enter for both ports.")
    print("    The app automatically selects two free localhost ports.")
    print("    No Termius port forwarding is needed.")
    print()
    print("  VPS / TERMIUS")
    print("    Enter fixed ports, then forward those ports in Termius.")
    print()
    print("Example VPS setup:")
    print("    Web UI: 8080")
    print("    OAuth:  8765")
    print("=" * 68)
    print()

    ui = ask_port("Web UI port", "auto")
    while True:
        auth = ask_port("OAuth callback port", "auto")
        if auth != ui:
            return ui, auth
        print("The two ports must be different. Please choose another OAuth port.")

def load_credentials():
    if not TOKEN_FILE.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
        return creds if creds and creds.valid else None
    except Exception:
        return None


def save_credentials(creds):
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def get_google_email(creds):
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]


def create_auth_flow():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json is missing. Put the Google Desktop OAuth JSON "
            "file beside app.py."
        )

    # IMPORTANT: Keep this exact Flow object alive until the callback.
    # authorization_url() generates a PKCE code_verifier. If the callback
    # creates a new Flow object, that verifier is lost and Google returns:
    # "(invalid_grant) Missing code verifier."
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
    )
    flow.redirect_uri = f"http://{AUTH_HOST}:{AUTH_PORT}/oauth2callback"
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return flow, authorization_url


def auth_worker():
    try:
        creds = load_credentials()
        if creds:
            email = get_google_email(creds)
            with lock:
                state.update(
                    creds=creds,
                    email=email,
                    authenticated=True,
                    auth_url=None,
                    auth_error=None,
                    oauth_flow=None,
                )
            return

        flow, auth_url = create_auth_flow()
        with lock:
            state["oauth_flow"] = flow
            state["auth_url"] = auth_url
            state["auth_error"] = None
    except Exception as exc:
        with lock:
            state["auth_error"] = str(exc)


@app.get("/")
def index():
    with lock:
        snapshot = {
            "authenticated": state["authenticated"],
            "email": state["email"],
            "auth_url": state["auth_url"],
            "auth_error": state["auth_error"],
        }
    return render_template("index.html", state=snapshot)


@app.get("/api/status")
def status():
    with lock:
        return jsonify({
            "authenticated": state["authenticated"],
            "email": state["email"],
            "auth_url": state["auth_url"],
            "auth_error": state["auth_error"],
            "job": dict(state["job"]),
            "ui_port": UI_PORT,
            "auth_port": AUTH_PORT,
        })


@app.post("/api/start-auth")
def start_auth():
    threading.Thread(target=auth_worker, daemon=True).start()
    return jsonify({"ok": True})


@app.post("/api/create-drafts")
def create_drafts():
    with lock:
        if not state["authenticated"] or not state["creds"]:
            return jsonify({"ok": False, "error": "Authorize the Gmail account first."}), 401
        if state["job"]["running"]:
            return jsonify({"ok": False, "error": "A draft job is already running."}), 409

    data = request.get_json(silent=True) or {}
    recipient = str(data.get("recipient", "")).strip()
    first = str(data.get("first", "")).strip()
    last = str(data.get("last", "")).strip()
    count_raw = str(data.get("count", "")).strip()
    delay_raw = str(data.get("delay", "0.25")).strip()

    if not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", recipient):
        return jsonify({"ok": False, "error": "Enter a valid recipient email address."}), 400
    if not re.fullmatch(r"\d{4,17}", first):
        return jsonify({"ok": False, "error": "First number must contain 4–17 digits."}), 400
    if not re.fullmatch(r"\d{4,17}", last):
        return jsonify({"ok": False, "error": "Last number must contain 4–17 digits."}), 400

    first_n, last_n = int(first), int(last)
    if first_n > last_n:
        return jsonify({"ok": False, "error": "First number must be less than or equal to last number."}), 400

    try:
        count = int(count_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "Draft count must be a whole number."}), 400
    if not 1 <= count <= 500:
        return jsonify({"ok": False, "error": "Draft count must be between 1 and 500 per run."}), 400

    try:
        delay = float(delay_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "Delay must be a number of seconds."}), 400
    if not 0 <= delay <= 60:
        return jsonify({"ok": False, "error": "Delay must be between 0 and 60 seconds."}), 400

    threading.Thread(
        target=create_draft_job,
        args=(recipient, first_n, last_n, count, delay),
        daemon=True,
    ).start()
    return jsonify({"ok": True})


@app.post("/api/stop")
def stop_job():
    with lock:
        state["job"]["stop_requested"] = True
    return jsonify({"ok": True})


def create_draft_job(recipient, first_n, last_n, count, delay):
    with lock:
        state["job"] = {
            "running": True,
            "requested": count,
            "created": 0,
            "failed": 0,
            "current_subject": "",
            "error": "",
            "done": False,
            "stop_requested": False,
        }
        creds = state["creds"]
        sender = state["email"]

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

        for i in range(count):
            with lock:
                if state["job"]["stop_requested"]:
                    break

            subject = str(random.randint(first_n, last_n))
            message = EmailMessage()
            message["To"] = recipient
            message["From"] = sender
            message["Subject"] = subject
            message.set_content("")

            encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
            try:
                service.users().drafts().create(
                    userId="me",
                    body={"message": {"raw": encoded}},
                ).execute()
                with lock:
                    state["job"]["created"] += 1
                    state["job"]["current_subject"] = subject
            except HttpError as exc:
                with lock:
                    state["job"]["failed"] += 1
                    state["job"]["error"] = str(exc)

            if i < count - 1 and delay:
                time.sleep(delay)
    except Exception as exc:
        with lock:
            state["job"]["error"] = str(exc)
    finally:
        with lock:
            state["job"]["running"] = False
            state["job"]["done"] = True


def run_oauth_callback_server():
    from werkzeug.serving import make_server

    callback_app = Flask("gmail_oauth_callback")

    @callback_app.get("/oauth2callback")
    def oauth_callback():
        try:
            if "error" in request.args:
                with lock:
                    state["auth_error"] = request.args.get("error")
                return "<h2>Authorization was cancelled or denied.</h2><p>You can close this tab.</p>"

            if "code" not in request.args:
                return "<h2>Missing authorization code.</h2>", 400

            # Reuse the exact Flow that generated the Google authorization
            # URL. This preserves both PKCE code_verifier and OAuth state.
            with lock:
                flow = state.get("oauth_flow")

            if flow is None:
                return (
                    "<h2>Authorization session expired.</h2>"
                    "<p>Return to the web UI and generate a new authorization link.</p>",
                    400,
                )

            flow.fetch_token(authorization_response=request.url)

            creds = flow.credentials
            save_credentials(creds)
            email = get_google_email(creds)

            with lock:
                state.update(
                    creds=creds,
                    email=email,
                    authenticated=True,
                    auth_url=None,
                    auth_error=None,
                    oauth_flow=None,
                )

            return """
            <!doctype html>
            <html><body style="font-family:system-ui;padding:40px">
            <h2>Gmail authorization successful.</h2>
            <p>You can close this tab and return to the Gmail Bulk Draft Builder.</p>
            </body></html>
            """
        except Exception as exc:
            with lock:
                state["oauth_flow"] = None
                state["auth_error"] = str(exc)
            return f"<h2>Authorization failed.</h2><pre>{str(exc)}</pre>", 500

    make_server(AUTH_HOST, AUTH_PORT, callback_app, threaded=True).serve_forever()


def main():
    global UI_PORT, AUTH_PORT

    UI_PORT, AUTH_PORT = choose_ports()

    threading.Thread(target=run_oauth_callback_server, daemon=True).start()
    threading.Thread(target=auth_worker, daemon=True).start()

    print()
    print("=" * 68)
    print(" Gmail Bulk Draft Builder")
    print("=" * 68)
    print(f" Web UI:          http://{UI_HOST}:{UI_PORT}")
    print(f" OAuth callback:  http://{AUTH_HOST}:{AUTH_PORT}/oauth2callback")
    print()
    print("If this app is running directly on your iPhone/iSH:")
    print(f"  Open: http://127.0.0.1:{UI_PORT}")
    print("  No Termius port forwarding is required.")
    print()
    print("If this app is running on your VPS:")
    print("  Forward these two remote ports in Termius:")
    print(f"    local {UI_PORT}  -> remote 127.0.0.1:{UI_PORT}")
    print(f"    local {AUTH_PORT} -> remote 127.0.0.1:{AUTH_PORT}")
    print(f"  Then open: http://127.0.0.1:{UI_PORT}")
    print("=" * 68)
    print()

    app.run(host=UI_HOST, port=UI_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
