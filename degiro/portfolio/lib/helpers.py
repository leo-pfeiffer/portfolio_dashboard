import datetime
import json
import smtplib
import email

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import ssl
from .api.settings import paths


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


def send_email(recipients: str, subject: str, body: str, filename: str):
    conf_path = paths.SETTINGS + '/mail.json'
    conf = json.load(open(conf_path))

    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = conf['email']  # Enter your address
    # receiver_email = recipients
    receiver_email = "leopold.pfeiffer@gmx.de"
    password = conf['password']

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    if filename is not None:
        # Open PDF file in binary mode
        with open(filename, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        message.attach(part)

    text = message.as_string()

    # Log in to server using secure context and send email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
