import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@noianalyzer.com")

def send_report_email(to_email: str, presigned_url: str, max_retries: int = 3):
    subject = "Your NOI Analyzer Report is Ready"
    content = (
        "Hello,\n\nYour NOI analysis report is ready. "
        "You can download it with the link below (valid for 1 hour):\n"
        f"{presigned_url}\n\n" "Thank you for using NOI Analyzer!"
    )

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content,
    )

    attempt = 0
    while attempt < max_retries:
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
            return
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                print(f"Email send failed after {max_retries} attempts: {e}")
                raise
            time.sleep(2 ** attempt) 