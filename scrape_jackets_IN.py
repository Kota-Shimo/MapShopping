import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import urllib.parse
import requests

# =============================================
# ★Firebase初期化処理★
# =============================================
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# =============================================
# ★ターゲットURLと設定★
# =============================================
base_url = "https://store.in-net.gr.jp/category/DOWN_M/"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "印_裏寺本店_セレクトショップ"
category_id = "down jacket"

# =============================================
# ★ヘルパー関数★
# =============================================
def get_soup(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def extract_color_from_url(url):
    # URL中にROUNDABOUTIN_COLOR=XXXがあればXXX部分を抽出
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    color_param = query_params.get("ROUNDABOUTIN_COLOR")
    if color_param and len(color_param) > 0:
        return color_param[0]
    return "No Color"

def parse_price(text):
    # 例："¥20,900円" → "20900"
    clean_text = re.sub(r"[¥,円]", "", text)
    try:
        price = float(clean_text)
    except:
        price = 0.0
    return price

def parse_products_from_soup(soup):
    products_data = []
    product_boxes = soup.select("#itemListSimple .box")
    for pb in product_boxes:
        link_tag = pb.select_one("a[href]")
        if not link_tag:
            continue
        product_url = urllib.parse.urljoin(base_url, link_tag.get("href"))

        # 商品名
        name_tag = pb.select_one("h3")
        product_name = name_tag.get_text(strip=True) if name_tag else "No Name"

        # ブランド
        brand_tag = pb.select_one("h4.brand")
        brand_name = brand_tag.get_text(strip=True) if brand_tag else ""

        # 価格
        price_tag = pb.select_one("p.price_en")
        price_text = price_tag.get_text(strip=True) if price_tag else "0"
        price = parse_price(price_text)

        # 画像URL
        img_tag = pb.select_one(".img_box img")
        if img_tag:
            img_url = img_tag.get("src")
            if img_url and img_url.startswith("/"):
                img_url = urllib.parse.urljoin(base_url, img_url)
        else:
            img_url = fallback_image_url

        # カラー情報をURLから取得
        color = extract_color_from_url(product_url)

        # サイズ情報：現状は空リスト。詳細ページにアクセスして取得可能
        sizes = []

        products_data.append({
            "product_name": product_name,
            "brand_name": brand_name,
            "price": price,
            "image_url": img_url,
            "product_url": product_url,
            "category_id": category_id,
            "store_id": store_id,
            "color": color,
            "sizes": sizes
        })
    return products_data

def get_next_page_url(soup):
    next_link = soup.select_one(".pagelink .next a")
    if next_link:
        next_url = next_link.get("href")
        if next_url:
            return urllib.parse.urljoin(base_url, next_url)
    return None

# =============================================
# ★スクレイピング処理本体★
# =============================================
all_products = []
try:
    driver = webdriver.Chrome(service=service)
    current_url = base_url

    while True:
        driver.get(current_url)
        time.sleep(3)  # 読み込み待機
        soup = get_soup(driver)

        products_on_page = parse_products_from_soup(soup)
        if not products_on_page:
            # 商品が取得できない場合は終了
            break

        all_products.extend(products_on_page)

        # 次ページチェック
        next_page_url = get_next_page_url(soup)
        if not next_page_url:
            break
        else:
            current_url = next_page_url

    print("全ページの商品取得が完了しました。")

except Exception as e:
    print(f"ページ取得中にエラーが発生しました: {e}")
    exit()
finally:
    driver.quit()

# =============================================
# ★Firestoreへ保存★
# =============================================
batch = db.batch()
index = 0
for product in all_products:
    doc_id = re.sub(r"[/\\ ]+", "_", product["product_name"] + "_" + product["brand_name"] + "_" + str(index))
    doc_ref = db.collection("stores").document(product["store_id"]).collection("items").document(doc_id)
    doc_data = {
        "product_name": product["product_name"],
        "brand_name": product["brand_name"],
        "price": product["price"],
        "category_id": product["category_id"],
        "store_id": product["store_id"],
        "color": product["color"],
        "sizes": product["sizes"],
        "image_url": product["image_url"],
        "product_url": product["product_url"]
    }
    batch.set(doc_ref, doc_data)
    index += 1

try:
    batch.commit()
    print("Firestoreへの商品データ保存が完了しました。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
