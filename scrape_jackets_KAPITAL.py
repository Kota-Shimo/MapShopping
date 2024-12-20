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

base_url = "https://www.kapital-webshop.jp/category/M_JACKET/"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/600x600.png?text=No+Image"
store_id = "KAPITAL KYOTO"
category_id = "jackets"

driver = None
try:
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    product_items = soup.select('#itemListImage .item_list_box')

    final_variants = []
    pid_counter = 0

    for item in product_items:
        pid_counter += 1
        # 商品名
        name_tag = item.select_one('.item_name a')
        product_name = name_tag.get_text().strip() if name_tag else "No Name"

        # 価格
        price_tag = item.select_one('.item_price')
        price_text = price_tag.get_text().strip() if price_tag else "0円"
        price_match = re.search(r'([\d,]+)円', price_text)
        if price_match:
            price = int(price_match.group(1).replace(',', ''))
        else:
            price = 0

        # メイン画像URL (カラーが無い場合に使用)
        main_img_tag = item.select_one('.img_box .img_inner img')
        main_image_url = main_img_tag.get('src') if main_img_tag else fallback_image_url
        if main_image_url.startswith('/'):
            main_image_url = 'https://www.kapital-webshop.jp' + main_image_url

        # カラー毎の画像取得
        # color_listに各カラーの画像と名称がある場合
        color_list_items = item.select('.color_list li')

        if not color_list_items:
            # カラー違いがない場合
            colors = ["No Color"]
            images = [main_image_url]
        else:
            colors = []
            images = []
            for li_item in color_list_items:
                color_name_el = li_item.select_one('p')
                c_name = color_name_el.get_text().strip() if color_name_el else "No Color"

                # カラーごとの画像URL取得
                color_img_tag = li_item.select_one('.img_inner img')
                if color_img_tag:
                    c_image_url = color_img_tag.get('src')
                    if c_image_url.startswith('/'):
                        c_image_url = 'https://www.kapital-webshop.jp' + c_image_url
                else:
                    c_image_url = fallback_image_url

                colors.append(c_name)
                images.append(c_image_url)

        # サイズ情報はページから取得できないので空
        sizes = []

        # カラーごとにvariant作成
        for c_name, c_img in zip(colors, images):
            variant = {
                "product_id": str(pid_counter),
                "product_name": product_name,
                "price": price,
                "category_id": category_id,
                "store_id": store_id,
                "color": c_name,
                "size": None,
                "image_id": None,
                "featured_image": c_img,
                "image_map": {}
            }
            final_variants.append(variant)

    # Firestore保存処理
    batch = db.batch()
    index = 0
    for v in final_variants:
        safe_pid = v["product_id"].replace("/", "_")
        safe_color = v["color"].replace("/", "_").replace(" ", "_")
        doc_id = f"{safe_pid}_{safe_color}"

        doc_ref = db.collection("stores").document(v["store_id"]).collection("items").document(doc_id)
        doc_data = {
            "product_name": v["product_name"],
            "price": v["price"],
            "category_id": v["category_id"],
            "store_id": v["store_id"],
            "color": v["color"],
            "sizes": [],  # サイズ情報不明なので空
            "image_url": v["featured_image"]
        }
        batch.set(doc_ref, doc_data)
        index += 1

    batch.commit()
    print("カラー毎に異なる画像を取得し、Firestoreに保存しました。")

except Exception as e:
    print(f"エラーが発生しました: {e}")
finally:
    if driver:
        driver.quit()
