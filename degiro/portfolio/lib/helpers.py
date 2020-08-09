import datetime
import json
import numpy as np
from scipy.stats import norm, t
import smtplib

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import ssl
from .api.settings import paths


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)


def send_email(receiver_email: str, subject: str, body: str, filename: str):
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


# Measures ---

def returns(series):
    return {returns.__name__: (series[-1] / series[0]) - 1}


def annualized_returns(series):
    return {annualized_returns.__name__: (series[-1] / series[0]) ** (252 / len(series)) - 1}


def std(series):
    return {std.__name__: np.std(series.pct_change(), ddof=1) * np.sqrt(252)}


def sharpe(series):
    mean = annualized_returns(series)["annualized_returns"]
    sd = std(series)["std"]
    rf = pd.read_csv("yahoo_data.csv", index_col="Date", parse_dates=True)["^IRX"][series.index[0]:series.index[-1]]
    ex_return = mean - np.mean(rf)
    return {sharpe.__name__: ex_return / sd}


def var(series):
    series = series.pct_change().dropna()
    mean = np.mean(series)
    sd = np.std(series)

    return {var.__name__: norm.ppf(0.01, loc=mean, scale=sd)}


def cvar(series):
    series = series.pct_change()
    mean = np.mean(series)
    sd = np.std(series)

    return {cvar.__name__: mean - 0.01 ** (-1) * sd * norm.pdf(norm.ppf(0.01))}


def max_drawdown(series):
    window = len(series)
    roll_max = series.rolling(window, min_periods=1).max()
    daily_drawdown = series / roll_max - 1
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()

    return {max_drawdown.__name__: min(max_daily_drawdown)}
