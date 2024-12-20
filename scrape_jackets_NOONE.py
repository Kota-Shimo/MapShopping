import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# Firebase初期化 (既に初期化済みの場合はスキップ)
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 取得元URL (ニットカテゴリを例)
base_url = "https://www.noone-shop.com/shop/knit/27"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "store_002"
category_id = "knit"

try:
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)

    # JavaScriptレンダリング待ち
    time.sleep(5)

    # スクロールダウン(必要なら数回行って全商品をロードさせる)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 商品一覧セレクタを確認
    product_items = soup.select('.so-product-grid__item')

    if not product_items:
        print("商品が取得できませんでした。")
        # HTMLを確認するため、一時的にHTMLをファイルに保存するなどして確認も可能
        # with open('debug.html', 'w', encoding='utf-8') as f:
        #     f.write(str(soup))
    else:
        final_data = []
        for product_div in product_items:
            # 商品名
            title_elem = product_div.select_one('.so-product-grid__title')
            product_name = title_elem.get_text(strip=True) if title_elem else "No Name"

            # 価格取得
            price_elem = product_div.select_one('.so-product-grid__price')
            product_price = 0
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # "¥15,000" → "15000"に変換
                product_price_str = re.sub(r'[^0-9]', '', price_text)
                if product_price_str.isdigit():
                    product_price = int(product_price_str)

            # 画像取得
            img_elem = product_div.select_one('.so-product-grid__image img')
            product_image_url = fallback_image_url
            if img_elem and img_elem.has_attr('src'):
                product_image_url = img_elem['src']
                if product_image_url.startswith('//'):
                    product_image_url = 'https:' + product_image_url

            # 詳細ページURL
            link_elem = product_div.select_one('a.so-product-grid__link')
            product_url = None
            if link_elem and link_elem.has_attr('href'):
                product_url = link_elem['href']
                if product_url.startswith('/'):
                    product_url = "https://www.noone-shop.com" + product_url

            # 色、サイズは一覧では不明なため一旦空
            color = "No Color"
            size = None

            product_data = {
                "product_name": product_name,
                "price": product_price,
                "category_id": category_id,
                "store_id": store_id,
                "color": color,
                "sizes": [size] if size else [],
                "image_url": product_image_url,
                "product_url": product_url
            }
            final_data.append(product_data)

        # Firestoreへ保存
        batch = db.batch()
        for index, pdata in enumerate(final_data):
            doc_id = re.sub(r'[^\w_-]+', '_', pdata["product_name"])
            doc_ref = db.collection("stores").document(pdata["store_id"]).collection("items").document(doc_id)
            batch.set(doc_ref, pdata)

        try:
            batch.commit()
            print("スクレイピングデータをFirestoreに保存しました。")
        except Exception as e:
            print(f"Firestore保存中にエラーが発生しました: {e}")

finally:
    driver.quit()
