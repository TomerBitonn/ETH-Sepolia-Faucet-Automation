import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO


# Send Email
def send_email(subject, body, attachment_path=None):

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header( "Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        logging.info(f"Email sent to {EMAIL_TO}")


# Waits until either 'drip in queue' or 'drip complete' appears
def wait_for_status(page, timeout=30000):
    """
    Waits until either 'drip in queue' or 'drip complete' appears.
    Returns 'pending', 'success', or 'failed'.
    """
    start = time.time()
    while time.time() - start < timeout / 1000:  # Convert ms to seconds
        try:
            # Check for success messages
            success_locator = page.locator("text=/drip complete|tokens sent|Testnet tokens sent/i")
            if success_locator.count() > 0 and success_locator.first.is_visible():
                logging.info("[SUCCESS] Faucet request completed successfully")
                return "success"

            # Check for pending messages
            pending_locator = page.locator("text=/on the way|drip in queue|few moments/i")
            if pending_locator.count() > 0 and pending_locator.first.is_visible():
                logging.info("Transaction detected: Faucet request is pending")
                time.sleep(2)
                continue

        except Exception as e:
            logging.debug(f"Status check iteration failed: {e}")

        time.sleep(1)  # Wait between checks

    logging.error("Timeout: no success message detected in time")
    return "failed"
