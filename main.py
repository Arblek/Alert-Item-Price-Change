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
                    // 1. Extract Product Title
                    const title = document.querySelector('h1.product-title')?.textContent.trim() || null;

                    // 2. Extract Price as Float
                    const priceEl = document.querySelector('.price-current_2026');
                    let price = null;
                    if (priceEl) {
                        const dollars = priceEl.querySelector('strong')?.textContent.trim() || '';
                        const cents = priceEl.querySelector('sup')?.textContent.trim() || '';
                        const rawPrice = dollars ? `${dollars}${cents}` : priceEl.textContent.trim();
                        
                        // Strip currency symbols, commas (e.g., "1,228.99"), and whitespace before parsing
                        const cleaned = rawPrice.replace(/[^0-9.]/g, '');
                        const parsed = parseFloat(cleaned);
                        price = Number.isNaN(parsed) ? null : parsed;
                    }

                    // 3. Extract Item Number
                    const h2s = Array.from(document.querySelectorAll('h2.text-darkgray'));
                    const itemH2 = h2s.find(el => el.textContent.includes('Item#'));
                    const sku = itemH2?.querySelector('em')?.textContent.trim() || null;

                    return {
                        sku,
                        price,
                        title
                    };
                })()
            """
NEWEGG_SELECTOR = "h1.product-title"

BESTBUY_QUERY = """
        (() => {
            // 1. Product Title
            const title = document.querySelector('[data-component-name="ProductHeader"] h1')?.textContent.trim() || null;

            // 2. Price as Float (uses the accessible .sr-only span "$479.99")
            const priceText = document.querySelector('[data-testid="price-block-customer-price"] .sr-only')?.textContent
                || document.querySelector('[data-testid="price-block-customer-price"]')?.textContent
                || '';
            const cleaned = priceText.replace(/[^0-9.]/g, '');
            const parsed = parseFloat(cleaned);
            const price = Number.isNaN(parsed) ? null : parsed;

            // 3. SKU (finds the div inside ProductHeader starting with "SKU:")
            const headerDivs = Array.from(document.querySelectorAll('[data-component-name="ProductHeader"] div'));
            const skuDiv = headerDivs.find(el => el.children.length === 0 && el.textContent.trim().startsWith('SKU:'));
            const sku = skuDiv ? skuDiv.textContent.replace(/^SKU:\\s*/i, '').trim() : null;

            return { sku, price, title };
        })()
    """
BESTBUY_SELECTOR = '[data-component-name="ProductHeader"] h1'

SITES = {
    "newgg.gg": (NEWEGG_QUERY, NEWEGG_SELECTOR),
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

                    if not sku or price is None:
                        raise ValueError(f"Incomplete scrape: {product}")

                    insert_product(connection, sku, title, price)

                    print(sku, " ", title)
                    subject = "Price dropped"
                    message = f"The price for {title} dropped. Current price is {price}. {url}"
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
