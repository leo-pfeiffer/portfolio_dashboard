from project.settings import MAIL

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import smtplib
import ssl


class Mail:

    smtp_server = MAIL['SMTP']
    sender_email = MAIL['EMAIL']
    password = MAIL['PASSWORD']

    @classmethod
    def send(cls, receiver_email: str, subject: str, body: str, filename: str = None):

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = cls.sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Add body to email
        message.attach(MIMEText(body, "plain"))

        if filename is not None:
            with open(filename, "rb") as attachment:
                part = MIMEApplication(attachment.read(), _subtype="pdf")

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )

            message.attach(part)

        text = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(cls.smtp_server, 465, context=context) as server:
            server.login(cls.sender_email, cls.password)
            server.sendmail(cls.sender_email, receiver_email, text)


