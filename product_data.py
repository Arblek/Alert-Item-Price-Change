from seleniumbase import sb_cdp


def looks_blocked(html: str) -> bool:
    low = html.lower()
    return (
        len(html) < 5000
        or "access denied" in low
        or ("reference #" in low and "akamai" in low)
        or "are you a human" in low
        or "px-captcha" in low
    )


def scrape_product_cdp(sb: sb_cdp.Chrome, url: str, query: str, wait_selector: str):
    sb.goto(url)
    sb.solve_captcha()

    sb.wait_for_element_present(wait_selector, timeout=20)
    data = sb.evaluate(query)

    if looks_blocked(sb.get_page_source()):
        raise "Blocked"
    else:
        return data
