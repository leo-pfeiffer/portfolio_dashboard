import datetime
import json
import smtplib
import pandas as pd

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import ssl
from .api.settings import paths
from .performance_measures import returns, annualized_returns, std, sharpe, var, max_drawdown


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


def send_email(receiver_email: str, subject: str, body: str, filename=None):

    conf_path = paths.SETTINGS + '/mail.json'
    conf = json.load(open(conf_path))

    smtp_server = conf['smtp']
    sender_email = conf['email']
    password = conf['password']

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
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
    with smtplib.SMTP_SSL(smtp_server, 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)


def measure_loop(portfolio_df: pd.Series) -> dict:
    switcher = {
        1: returns,
        2: annualized_returns,
        3: std,
        4: sharpe,
        5: var,
        6: max_drawdown,
    }

    data = {}
    for key in switcher.keys():
        measure = switcher.get(key)
        data = {**data, **measure(portfolio_df)}

    return data

# portfolio_df = get_portfolio().iloc[:, 8]
# result = measure_loop(portfolio_df)
