import os
import sqlite3
import smtplib
from dotenv import load_dotenv
from database import query_first

def alert_price(connection: sqlite3.Connection, sku: str, price_less_than: float,recipient_email: str, subject:str , message: str):
    try:
        price = query_first(connection, sku)
        if compare_price(price[0][0], price_less_than):
            print("Price dropped")
            send_email(recipient_email, subject, message)
    except Exception as e:
        print(f"Error: {e}")


def compare_price(price: float, price_less_than: float) -> bool:
    if price < price_less_than:
        return True         #Price dropped
    return False            #Price did not drop


def send_email(recipient_email: str, subject:str , message: str):
    load_dotenv()
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    text = f"Subject: {subject} \n\n {message}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(email, password)
        server.sendmail(email, recipient_email, text)
        print("Email sent")
    except smtplib.SMTPServerDisconnected:
        print("SMTP Server error")
