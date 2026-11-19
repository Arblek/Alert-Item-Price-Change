import os
from dotenv import load_dotenv
from product_data import site_newegg
from price_alert import alert_price
from database import get_connection, create_table, insert_product, query_data, delete_table, query_first_two

LINK = "https://www.newegg.com/crucial-1tb-p310-nvme-2-0/p/N82E16820156416"

def all_unique_sku(connection) -> set:
    data_list = query_data(connection)
    unique_skus = set()

    for data in data_list:
        unique_skus.add((data[1],data[2]))
    return unique_skus

def main():
    load_dotenv()
    #product = site_newegg(LINK)
    connection = get_connection("products.db")


    try:
        create_table(connection)
        #insert_product(connection, product.get("sku"), product.get("title"), product.get("price"), ( 1 if product.get("stock") else 0))
        #insert_product(connection, "N82E16820156416", "Crucial P310 2280 1TB PCIe Gen4 NVMe Gaming PS5 SSD with Heatsink, Up to 7,100MB/s, PlayStation5, Laptop & Desktop (PC) Compatible, Solid State Drive - CT1000P310SSD5-01", 11.32, 1)

        unique_skus = all_unique_sku(connection)
        for sku, title in unique_skus:
            print(sku, " ", title)
            subject = "Price dropped"
            message = f"The price for {title} dropped"
            alert_price(connection, sku, os.getenv("EMAIL"), subject, message)
    finally:
        connection.close()

main()