from curl_cffi import requests as cffi_req
import json


def request_info(url: str, headers: dict | None = None) -> dict:
    request = cffi_req.get(
        url,
        headers=headers,
        impersonate="chrome",
        timeout=30,)
        

    return request.json()


def site_newegg(url: str) -> dict:
    product_sku = url.split('/')[-1]
    API = f"https://www.newegg.com/product/api/ProductRealtime?ItemNumber={product_sku}"

    data = request_info(API)
    item = data.get("MainItem")
    product_info = {
        "sku": product_sku,
        "title": item.get("Description" or {}).get("Title"),
        "price": float(item.get("FinalPrice")), 
        "stock": bool(item.get("Instock"))
    }

    return product_info

