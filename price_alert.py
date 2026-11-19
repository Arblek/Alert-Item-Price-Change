import os
import sqlite3
import smtplib
from dotenv import load_dotenv
from database import query_first_two

def alert_price(connection: sqlite3.Connection, sku: str, recipient_email: str, subject:str , message: str):
    try:
        price1, price2 = query_first_two(connection, sku)
        if compare_price(price1[0], price2[0]):
            print("Price dropped")
            send_email(recipient_email, subject, message)
    except Exception as e:
        print(f"Error: Cant compare only one entry for the same SKU, minimum two needed {e}")


def compare_price(price1: float, price2: float) -> bool:
    if price1 < price2:
        return True         #Price dropped
    return False            #Price did not drop


def send_email(recipient_email: str, subject:str , message: str):
    load_dotenv()
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    text = f"Subject: {subject} \n\n {message}"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(email, password)
    server.sendmail(email, recipient_email, message)
    print("Email sent")
