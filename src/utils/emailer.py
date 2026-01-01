# src/utils/emailer.py

import smtplib
from email.message import EmailMessage
from pathlib import Path
import os
import tempfile


class EmailSender:

    def __init__(self, sender_email, app_password, receiver_email):
        self.sender_email = sender_email
        self.password = app_password
        self.receiver_email = receiver_email

    def _tail_file(self, src_path: Path, max_lines: int = 1000) -> Path:
        """Write last `max_lines` of `src_path` to a temp file and return its Path."""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_tail.csv")
        tmp_path = Path(tmp.name)
        tmp.close()

        # Efficient tail: read lines and keep last N
        with open(src_path, "r", errors="ignore") as inf, open(tmp_path, "w") as outf:
            from collections import deque

            dq = deque(inf, maxlen=max_lines)
            outf.writelines(dq)

        return tmp_path

    def send_log(self, file_path):
        """
        Sends CSV log file over email. If file is large (>EMAIL_MAX_ATTACHMENT_BYTES),
        attach only the last N lines to avoid SMTP size limits.
        Configure via env var `EMAIL_MAX_ATTACHMENT_BYTES` (default 20MB) and
        `EMAIL_TAIL_LINES` (default 1000).
        """

        msg = EmailMessage()
        msg["Subject"] = "Traffic AI Vehicle Detection Log"
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email

        file_path = Path(file_path)

        max_bytes = int(os.getenv("EMAIL_MAX_ATTACHMENT_BYTES", str(20 * 1024 * 1024)))
        tail_lines = int(os.getenv("EMAIL_TAIL_LINES", "1000"))

        if not file_path.exists():
            msg.set_content("No vehicle log found to attach.")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            print("[EMAIL] No log file found, sent notification email (no attachment)")
            return

        file_size = file_path.stat().st_size

        # If file is larger than allowed, attach a tail copy instead
        attach_path = file_path
        truncated = False
        tmp_path = None

        if file_size > max_bytes:
            truncated = True
            tmp_path = self._tail_file(file_path, max_lines=tail_lines)
            attach_path = tmp_path

        msg.set_content(
            "Attached is the vehicle detection CSV log from latest run.\n"
            + ("(Note: original log was large and has been truncated.)" if truncated else "")
        )

        with open(attach_path, "rb") as f:
            data = f.read()

        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=attach_path.name,
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.password)
                server.send_message(msg)

            print("[EMAIL] CSV log emailed successfully")
        finally:
            # cleanup temp file if created
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
