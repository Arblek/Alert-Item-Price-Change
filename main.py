import os
import json
from dotenv import load_dotenv
from product_data import site_newegg
from price_alert import alert_price
from database import get_connection, create_table, insert_product, query_data, delete_table, query_first


def all_unique_sku(connection) -> set:
    data_list = query_data(connection)
    unique_skus = set()

    for data in data_list:
        unique_skus.add((data[1],data[2]))
    return unique_skus

def main():
    with open("products.json", 'r') as file:
        product_data = json.load(file)
        for data in product_data:
            load_dotenv()
            product = site_newegg(data.get("url"))
            connection = get_connection("products.db")


            try:
                create_table(connection)
                insert_product(connection, product.get("sku"), product.get("title"), product.get("price"), ( 1 if product.get("stock") else 0))
                
                unique_skus = all_unique_sku(connection)
                for sku, title in unique_skus:
                    print(sku, " ", title)
                    subject = "Price dropped"
                    message = f"The price for {title} dropped"
                    alert_price(connection, sku, data.get("price_less_than"), os.getenv("EMAIL"), subject, message)
            finally:
                connection.close()

main()