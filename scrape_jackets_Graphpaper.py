import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from collections import defaultdict

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

base_url = "https://graphpaper-kyoto.com/collections/mens/knit"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "Graphpaper kyoto"
category_id = "knit"

try:
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    product_divs = soup.find_all('div', class_='product-grid-item')
    products_data = []

    for product_div in product_divs:
        # 商品名取得
        title_tag = product_div.select_one('.product-grid-item__title')
        if not title_tag:
            continue
        product_name = title_tag.get_text(strip=True)

        # 価格取得
        price_tag = product_div.select_one('.product-grid-item__price')
        price_text = price_tag.get_text(strip=True) if price_tag else "No Price"
        # 価格を数値変換（円マーク削除、カンマ削除）
        price_value = 0.0
        price_match = re.search(r'¥([\d,]+)', price_text)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            price_value = float(price_str)

        # 画像URL取得（background-imageから抽出）
        image_div = product_div.select_one('.product__media.product__media--featured')
        img_url = fallback_image_url
        if image_div and 'style' in image_div.attrs:
            style_str = image_div['style']
            bg_match = re.search(r'url\(([^)]+)\)', style_str)
            if bg_match:
                img_url = bg_match.group(1).strip('"').strip("'")
        
        # カラーやサイズなどの詳細は商品詳細ページでなければ取得困難。
        # ここでは省略。
        
        # Firestoreに格納するためのデータ作成
        product_data = {
            "product_name": product_name,
            "price": price_value,
            "category_id": category_id,
            "store_id": store_id,
            "color": "N/A",
            "sizes": [],
            "image_url": img_url
        }
        products_data.append(product_data)

    # Firestoreへの書き込み
    batch = db.batch()
    index = 0
    for pdata in products_data:
        # doc_idに使えるようにファイル名などを整形
        safe_name = re.sub(r'\W+', '_', pdata["product_name"]).lower()
        doc_id = f"{store_id}_{category_id}_{safe_name}"

        doc_ref = db.collection("stores").document(pdata["store_id"]).collection("items").document(doc_id)
        batch.set(doc_ref, pdata)
        index += 1

    try:
        batch.commit()
        print("Firestoreへの保存が完了しました。")
    except Exception as e:
        print(f"Firestore保存中にエラーが発生しました: {e}")
except Exception as e:
    print(f"取得中にエラーが発生しました: {e}")
finally:
    driver.quit()
