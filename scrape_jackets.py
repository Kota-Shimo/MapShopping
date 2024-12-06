import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# Firebaseの初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Seleniumで動的に生成されるページを取得
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)
url = "https://www.hufworldwide.jp/collections/jackets"

try:
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    time.sleep(5)  # ページの完全な読み込みを待機
    html = driver.page_source
    driver.quit()
    print("動的なページの取得に成功しました！")
except Exception as e:
    print(f"動的ページの取得中にエラーが発生しました: {e}")
    exit()

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html, 'html.parser')

# 1. JSONデータを取得して解析
script_tag = soup.find('script', string=lambda x: x and "ShopifyAnalytics.meta" in x)
if not script_tag:
    print("適切なスクリプトタグが見つかりませんでした。")
    exit()

try:
    script_content = script_tag.string.strip()
    json_data_match = re.search(r"var meta = (.*);", script_content)
    if json_data_match:
        json_data = json_data_match.group(1)
        data = json.loads(json_data)
        products_from_json = data.get("products", [])
    else:
        print("JSONデータの抽出に失敗しました。")
        exit()
except Exception as e:
    print(f"JSONデータの解析中にエラーが発生しました: {e}")
    exit()

# 2. HTMLから商品情報を取得（画像など）
product_divs = soup.find_all('div', class_='boost-sd__product-item')
products_from_html = []

if not product_divs:
    print("HTMLから商品情報が見つかりませんでした。セレクタを確認してください。")
else:
    for product_div in product_divs:
        img_tag = product_div.find('img', class_='boost-sd__product-image-img')
        product_name = img_tag.get('alt', 'No Name') if img_tag else 'No Name'
        product_image_url = img_tag.get('src') if img_tag else None
        if product_image_url and product_image_url.startswith('//'):
            product_image_url = 'https:' + product_image_url
        products_from_html.append({
            "name": product_name,
            "image_url": product_image_url
        })

# 3. JSONデータとHTMLデータを統合
final_products = []
store_id = "store_002"
category_id = "jackets"

for product_json in products_from_json:
    for variant in product_json["variants"]:
        variant_name = variant["name"]
        variant_price = variant["price"] / 100  # 価格はセント単位なので変換
        image_url = None

        # HTMLデータから一致する画像を探す
        for html_product in products_from_html:
            if html_product["name"].lower() in variant_name.lower():
                image_url = html_product["image_url"]
                break

        final_products.append({
            "variant_name": variant_name,
            "price": variant_price,
            "image_url": image_url,
            "category_id": category_id,
            "store_id": store_id,
            "tags": re.findall(r'\b\w+\b', variant_name.lower())
        })

# 4. Firestoreに保存
batch = db.batch()
for idx, product in enumerate(final_products):
    doc_ref = db.collection("stores").document(store_id).collection("items").document(str(idx))
    batch.set(doc_ref, product)

try:
    batch.commit()
    print(f"商品情報を {store_id} の`items`サブコレクションに保存しました！")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
