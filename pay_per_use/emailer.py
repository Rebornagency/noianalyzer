import os
import time

# Adapted to use the Resend transactional-email service instead of SendGrid
from resend import Resend


# NOTE: set this in your environment (e.g. .env file or hosting dashboard)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
# "from" address must be verified in your Resend dashboard or belong to a
# domain you have validated with Resend DNS records.
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@noianalyzer.com")

# Create a single reusable client (thread-safe according to Resend docs)
_resend_client: Resend | None = None


def _get_resend_client() -> Resend:
    global _resend_client
    if _resend_client is None:
        if not RESEND_API_KEY:
            raise EnvironmentError(
                "Missing RESEND_API_KEY environment variable. "
                "Set it to the API key you generate in the Resend dashboard."
            )
        _resend_client = Resend(api_key=RESEND_API_KEY)
    return _resend_client


def send_report_email(to_email: str, presigned_url: str, max_retries: int = 3):
    """Send an email with the secure report link using Resend.

    Parameters
    ----------
    to_email : str
        Recipient email address.
    presigned_url : str
        Presigned URL pointing to the generated report (valid 1 hour).
    max_retries : int, optional
        Simple exponential-backoff retry count for transient failures.
    """

    subject = "Your NOI Analyzer Report is Ready"
    content_text = (
        "Hello,\n\nYour NOI analysis report is ready. "
        "You can download it with the link below (valid for 1 hour):\n"
        f"{presigned_url}\n\n" "Thank you for using NOI Analyzer!"
    )

    email_payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "text": content_text,
    }

    attempt = 0
    while attempt < max_retries:
        try:
            client = _get_resend_client()
            client.emails.send(email_payload)
            return  # Success
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                print(f"Email send failed after {max_retries} attempts: {e}")
                raise
            # Simple exponential back-off: 2, 4, 8 … seconds
            time.sleep(2 ** attempt) 