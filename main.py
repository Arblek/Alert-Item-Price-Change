import os
import json
import time
import random
from dotenv import load_dotenv
from seleniumbase import sb_cdp
from product_data import scrape_product_cdp
from price_alert import alert_price
from database import (
    get_connection,
    create_table,
    insert_product,
    query_data,
)

PROFILE_DIR = "./pw_profile"

NEWEGG_QUERY = """
(() => {
        const item = window.__initialState__?.ItemDetail;

        const title = item?.Description?.Title
            || document.querySelector('h1.product-title')?.textContent.trim() || null;

        let price = typeof item?.FinalPrice === 'number' ? item.FinalPrice : null;
        if (price === null) {
            const priceEl = document.querySelector('.price-current_2026');
            const raw = priceEl?.textContent.replace(/[^0-9.]/g, '');
            const parsed = parseFloat(raw);
            price = Number.isNaN(parsed) ? null : parsed;
        }

        const sku = item?.Item
            || Array.from(document.querySelectorAll('h2.text-darkgray'))
                .find(el => el.textContent.includes('Item#'))?.querySelector('em')?.textContent.trim()
            || null;

        // 1 = in stock, 0 = out of stock, null = couldn't tell
        let in_stock = null;
        if (item && typeof item.Instock === 'boolean') {
            in_stock = (item.Instock && item.Stock > 0) ? 1 : 0;
        }

        return { sku, price, title, in_stock };
})()
            """
NEWEGG_SELECTOR = "h1.product-title"

BESTBUY_QUERY = """
(() => {
        const title = document.querySelector('[data-component-name="ProductHeader"] h1')?.textContent.trim() || null;

        const priceText = document.querySelector('[data-testid="price-block-customer-price"] .sr-only')?.textContent
            || document.querySelector('[data-testid="price-block-customer-price"]')?.textContent
            || '';
        const cleaned = priceText.replace(/[^0-9.]/g, '');
        const parsed = parseFloat(cleaned);
        const price = Number.isNaN(parsed) ? null : parsed;

        const headerDivs = Array.from(document.querySelectorAll('[data-component-name="ProductHeader"] div'));
        const skuDiv = headerDivs.find(el => el.children.length === 0 && el.textContent.trim().startsWith('SKU:'));
        const sku = skuDiv ? skuDiv.textContent.replace(/^SKU:\\s*/i, '').trim() : null;

    let in_stock = null;
    const fulfillmentEl = document.querySelector('[data-component-name="FulfillmentSelector"]');
    if (fulfillmentEl) {
        const shipping = Array.from(fulfillmentEl.querySelectorAll('[role="radio"]'))
            .find(el => /^\\s*shipping/i.test(el.textContent));
        if (shipping) {
            const dateLabel = shipping.querySelector('[data-testid="availabilityDateLabel"]')?.textContent.trim();
            if (/unavailable|not available|sold out|not in stock/i.test(shipping.textContent)) in_stock = 0;
            else if (dateLabel) in_stock = 1;
        }
    }

        return { sku, price, title, in_stock };
    })()
    """
BESTBUY_SELECTOR = '[data-component-name="ProductHeader"] h1'

SITES = {
    "newegg.com": (NEWEGG_QUERY, NEWEGG_SELECTOR),
    "bestbuy.com": (BESTBUY_QUERY, BESTBUY_SELECTOR),
}


def all_unique_sku(connection) -> set:
    data_list = query_data(connection)
    unique_skus = set()

    for data in data_list:
        unique_skus.add((data[1], data[2]))
    return unique_skus


def main():
    sb = sb_cdp.Chrome(
        headless=False,
        locale="en-US",
        user_data_dir=PROFILE_DIR,
    )

    with open("products.json", "r") as file:
        load_dotenv()
        product_data = json.load(file)
        connection = get_connection("products.db")

        try:
            create_table(connection)
            for data in product_data:
                url = data.get("url")
                try:
                    site = data.get("site")
                    if site not in SITES:
                        raise ValueError(
                            f"Unknown site {site!r}, expected one of {sorted(SITES)}"
                        )

                    query, selector = SITES[site]
                    product = scrape_product_cdp(sb, url, query, selector)

                    sku = product.get("sku")
                    title = product.get("title")
                    price = product.get("price")
                    stock = product.get("in_stock")

                    if not sku or price is None:
                        raise ValueError(f"Incomplete scrape: {product}")

                    insert_product(connection, sku, title, price, stock)

                    print(sku, " ", title)
                    subject = "Price dropped"
                    message = f"The price for {title} is below the set treshold of {data.get("price_less_than")}. Current price is {price}. {url}"

                    if product.get("in_stock") != 0:
                        alert_price(
                            connection,
                            sku,
                            data.get("price_less_than"),
                            os.getenv("EMAIL"),
                            subject,
                            message,
                        )
                    time.sleep(random.uniform(2, 5))
                except Exception as exc:
                    print(f"Error processing {url}: {exc}")
                    continue
        finally:
            connection.close()
            sb.quit()


if __name__ == "__main__":
    main()
