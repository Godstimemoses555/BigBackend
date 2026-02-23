from argon2 import PasswordHasher
import os
from dotenv import load_dotenv
import secrets
import smtplib


from argon2.exceptions import VerifyMismatchError
from passlib.context import CryptContext
from passlib.context import CryptContext



ph=PasswordHasher()
def hashedpassword(password):
    hashed=ph.hash(password)
    return hashed

def verifyHashed(hashedpassword,password):
    value=ph.verify(hashedpassword,password)
    return value  



pin_hasher = PasswordHasher()

def hash_secret_pin(pin: str) -> str:
    """Hashes a 4-digit PIN using argon2."""
    return pin_hasher.hash(pin)

def verify_secret_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verifies a plain PIN against a hashed PIN using argon2."""
    try:
        return pin_hasher.verify(hashed_pin, plain_pin)
    except VerifyMismatchError:
        return False




def send_email( receiver: str, subject: str, body: str):
    """
    Sends an email using Gmail SMTP.

    Args:
        sender (str): Sender email address.
        receiver (str): Receiver email address.
        subject (str): Email subject line.
        body (str): Email body text.
    """
    password = os.getenv("PASSWORD")  # Make sure PASSWORD exists in .env
    email = os.getenv("SENDER")


    # Create email structure
    message = MIMEMultipart()
    message["From"] = email
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send email
    try:
        with smtplib.SMTP("	smtp.mailmug.net", 587) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, receiver, message.as_string())
            print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)





load_dotenv()

def send_html_email( receiver: str, subject: str,id ):
    """
    Sends an HTML email using Gmail SMTP.

    Args:
        sender (str): Sender email address.
        receiver (str): Receiver email address.
        subject (str): Email subject line.
        html_content (str): HTML body (supports tags, CSS, links, buttons).
    """
    password = os.getenv("PASSWORD")  # Get app password from .env
    email = os.getenv("SENDER")

    # Email structure
    message = MIMEMultipart("alternative")  
    message["From"] = email
    message["To"] = receiver
    message["Subject"] = subject

    # Attach the HTML to the email
    message.attach(MIMEText(mainhtml(id), "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, receiver, message.as_string())
            print("HTML email sent successfully!")

    except Exception as e:
        print("Failed to send email:", e)




def generate_otp():
    """ Generate a secure 6 digit code."""
    return str(secrets.randbelow(1000000)).zfill(6)
   


