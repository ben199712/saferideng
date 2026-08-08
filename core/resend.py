import json
import urllib.error
import urllib.request


class ResendError(Exception):
    def __init__(self, status_code, message, response_body=""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


def send_resend_email(*, api_key, from_email, to_email, subject, html, text):
    if not api_key:
        raise ResendError(0, "RESEND_API_KEY is not configured.")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request("https://api.resend.com/emails", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            parsed = json.loads(body or "{}")
            message_id = parsed.get("id", "") or ""
            return message_id, body[:2000]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
        raise ResendError(getattr(exc, "code", 0) or 0, "Resend HTTP error", body[:2000])
    except urllib.error.URLError as exc:
        raise ResendError(0, f"Resend network error: {exc}")
