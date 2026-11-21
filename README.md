# Alert Item Price Change

A small Python script that checks product prices on **Newegg** and **Best Buy** and emails you
when a price is below your target and the item is not known to be out of stock.

Every run it opens Chrome (via [SeleniumBase](https://github.com/seleniumbase/SeleniumBase)),
visits each product in `products.json`, saves the price to a local SQLite database
(`products.db`), and sends an email if the price is below your target.

## Setup

1. Install Python 3.10+ and Google Chrome.
2. Install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create your `.env` file from the template and fill it in:

   ```bash
   cp .example.env .env
   ```

   | Variable | Meaning |
   |---|---|
   | `EMAIL` | Gmail address that sends the alerts. Alerts are sent from and to this address. |
   | `PASSWORD` | A Gmail **App Password**, not your normal password. Create one at <https://myaccount.google.com/apppasswords> (needs 2-Step Verification). |

## Choosing products: `products.json`

A list of products to watch:

```json
[
    {
        "url": "https://www.bestbuy.com/product/...",
        "price_less_than": 450,
        "site": "bestbuy.com"
    },
    {
        "url": "https://www.newegg.com/.../p/N82E16819113877",
        "price_less_than": 400,
        "site": "newegg.com"
    }
]
```

| Field | Meaning |
|---|---|
| `url` | The product page. |
| `price_less_than` | Email me when the price is **below** this number (an exact match does not alert). |
| `site` | Must be exactly `newegg.com` or `bestbuy.com`. Any other value is logged as an error and skipped. |

**Once the price drops and you've bought the item, remove it from `products.json`.** The script
sends an email on every run while the price stays below your target, so a repeated email is
a reminder that the product is still on the list. Removing an entry stops it from being
checked; its saved price history stays in `products.db`.

## Running

```bash
python main.py
```

A Chrome window opens (the script runs with `headless=False`) and visits each product with a
short random pause between pages. A browser profile is stored in `pw_profile/`.

To run it on a schedule, use cron (Linux/macOS) or Task Scheduler (Windows). For example, twice a day:

```cron
0 9,18 * * *  cd /path/to/Alert-Item-Price-Change && .venv/bin/python main.py >> run.log 2>&1
```

On a server without a screen, run it under a virtual display, e.g. `xvfb-run python main.py`.
Running it very often increases the chance the sites block you, so a few times a day is plenty.

## How stock is handled

| Site | What is checked |
|---|---|
| Newegg | The product's `Instock` and `Stock` values in the page data. |
| Best Buy | The **Shipping** option in the fulfillment box (store pickup is ignored because it depends on location). |

- A product that is **out of stock** is still recorded in the price history, but no email is sent.
- If stock **cannot be determined** (for example, a site changed its layout), the email is still sent.

## Data

Prices are stored in `products.db` (SQLite, table `products_data` with `id`, `sku`, `title`, `price`, `stock`).
The table is created automatically on first run. `products.db` is listed in `.gitignore`. If it is already
tracked in your clone, stop tracking it (this keeps your local file):

```bash
git rm --cached products.db
```

## Troubleshooting

| Message | What it means |
|---|---|
| `Error processing <url>: Unknown site ...` | `site` in `products.json` is misspelled. Use `newegg.com` or `bestbuy.com`. |
| `Error processing <url>: Blocked` | The site showed a captcha or access-denied page. Wait and try again later, and run less often. |
| `Error processing <url>: Incomplete scrape ...` | The page loaded but the title/SKU/price could not be read. The site may have changed its layout. |
| `Error: (535, ...)` / login failure | Wrong `EMAIL`/`PASSWORD`. Use a Gmail App Password. |

The scraper reads page markup and page data that the sites can change at any time, so it may need
updating. Automated access may be against a site's terms of service; use it at your own risk and keep the
check frequency low.
