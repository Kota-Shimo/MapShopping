import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

base_url = "https://studious.co.jp/shop/c/csm1115/"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "STUDIOUS_MENS_京都三条店"
category_id = "outerwear"

driver = None
products_list = []

try:
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_items = soup.select("ul.block-goods-list-d--items > li")
    for item in product_items:
        # 商品URL、ブランド、商品名、画像URL、価格を取得
        link_tag = item.select_one(".block-goods-list-d--image a")
        if not link_tag:
            continue

        product_url = link_tag.get("href")
        if product_url and product_url.startswith("/"):
            product_url = "https://studious.co.jp" + product_url

        img_tag = link_tag.select_one("img")
        product_image_url = img_tag.get("src") if img_tag else fallback_image_url
        if product_image_url.startswith("/"):
            product_image_url = "https://studious.co.jp" + product_image_url

        brand_tag = item.select(".block-goods-list-d--item-description-text .block-goods-list-d--goods-name a")
        if len(brand_tag) < 2:
            continue
        brand_name = brand_tag[0].get_text(strip=True)
        product_name = brand_tag[1].get_text(strip=True)

        price_tag = item.select_one(".block-goods-list-d--price")
        raw_price = price_tag.get_text(strip=True) if price_tag else "0"
        price_str = re.sub(r"[^\d]", "", raw_price)
        price = int(price_str) if price_str.isdigit() else 0

        product_id_match = re.search(r"/g/(g\d+)", product_url)
        product_id = product_id_match.group(1) if product_id_match else None

        product_data = {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand_name,
            "price": price,
            "category_id": category_id,
            "store_id": store_id,
            "color": None,
            "sizes": [],
            "image_url": product_image_url,
            "product_url": product_url
        }
        products_list.append(product_data)

    print("商品取得が完了しました。")
except Exception as e:
    print(f"ページ取得中にエラーが発生しました: {e}")
finally:
    if driver:
        driver.quit()

# Firestoreに保存
batch = db.batch()
for p in products_list:
    doc_id = p["product_id"] if p["product_id"] else p["product_name"][:20]
    doc_ref = db.collection("stores").document(p["store_id"]).collection("items").document(doc_id)
    batch.set(doc_ref, p)

try:
    batch.commit()
    print("Firestoreへの保存が完了しました。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
