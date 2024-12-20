import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from collections import defaultdict
import urllib.parse
import hashlib

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

base_url = "https://fascinate-online.com/category/4_coat_m/"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "FASCINATE KYOTO"
category_id = "coat"

def get_page_data(driver, url):
    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

try:
    driver = webdriver.Chrome(service=service)
    soup = get_page_data(driver, base_url)

    product_divs = soup.find_all('div', class_='catalogList_item')
    # product_divsは各商品を表すdiv要素
    # 商品一覧情報を格納するためのリスト
    products = []

    for product_div in product_divs:
        # 商品URL
        link_tag = product_div.find('a', class_='ga4_event_select_item')
        if not link_tag:
            continue
        product_url = link_tag.get('href', '').strip()
        if not product_url.startswith('http'):
            product_url = urllib.parse.urljoin(base_url, product_url)

        # 画像URL取得
        img_tag = product_div.find('div', class_='product-image').find('img')
        if img_tag:
            image_url = img_tag.get('src', '')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
        else:
            image_url = fallback_image_url
        
        # ブランド名
        brand_name_tag = product_div.find('p', class_='brandName')
        brand_name = brand_name_tag.text.strip() if brand_name_tag else "No Brand"
        
        # 商品名
        commodity_name_tag = product_div.find('p', class_='commodityName')
        commodity_name = commodity_name_tag.text.strip() if commodity_name_tag else "No Name"

        # 価格取得
        # 通常価格または特別価格(special_price)がある場合がある
        price = None
        price_line = product_div.find('div', class_='priceLine')
        if price_line:
            regular_price_tag = price_line.find('p', class_='regular_price')
            special_price_tag = price_line.find('p', class_='special_price')
            if special_price_tag:
                # special_price内の-saleまたはmember_priceを優先(商品による)
                sale_price_tag = special_price_tag.find('span', class_='-sale')
                member_price_tag = special_price_tag.find('span', class_='member_price')
                if sale_price_tag:
                    # "￥12,345"のような文字列から数字部分を抽出
                    price_text = sale_price_tag.get_text(strip=True)
                    price = int(re.sub(r'[^\d]', '', price_text)) if re.sub(r'[^\d]', '', price_text) else None
                elif member_price_tag:
                    # 会員価格は価格非公開の場合があるが、ここではスキップまたは0扱い
                    price = None
                else:
                    # special_priceタグ内に-saleがない場合は、子要素から探す
                    price_text = special_price_tag.get_text(strip=True)
                    digits = re.sub(r'[^\d]', '', price_text)
                    if digits:
                        price = int(digits)
            
            elif regular_price_tag:
                # レギュラー価格
                price_text = regular_price_tag.get_text(strip=True)
                digits = re.sub(r'[^\d]', '', price_text)
                if digits:
                    price = int(digits)

        # カラー情報取得（config-colortip_list_itemから）
        color_elements = product_div.select('ul.config-colortip_list li.config-colortip_list_item')
        colors = []
        for c_el in color_elements:
            # colorクラス例: colortip_color185など
            # 厳密な名前取得は困難な場合、クラス名から判断や上位テキストから取得可能
            # ここではデータ属性なし、altなしのため、クラス名や色名定義がわからなければ
            # 最後にあるstyleから判断は難しいためplaceholder対応
            # このサイト上では色名情報明示的にないため、HTML上テキストは持たないので簡易対応
            # 暫定的に"Unknown Color"とする
            colors.append("Unknown Color")
        if not colors:
            # カラー情報がない場合
            colors = ["No Color"]

        # データ構造整備
        product_data = {
            "brand_name": brand_name,
            "commodity_name": commodity_name,
            "price": price if price else 0,
            "category_id": category_id,
            "store_id": store_id,
            "colors": colors,
            "image_url": image_url,
            "product_url": product_url
        }
        products.append(product_data)

    # Firestoreへ保存
    batch = db.batch()
    index = 0
    for p in products:
        # 一意なID: hashなどで作成
        # brand_name + commodity_nameからsha1などでID生成
        raw_id = (p["brand_name"] + "_" + p["commodity_name"] + "_" + p["product_url"]).encode('utf-8')
        doc_id = hashlib.sha1(raw_id).hexdigest()

        doc_ref = db.collection("stores").document(p["store_id"]).collection("items").document(doc_id)
        doc_data = {
            "product_name": p["commodity_name"],
            "brand_name": p["brand_name"],
            "price": p["price"],
            "category_id": p["category_id"],
            "store_id": p["store_id"],
            "color": p["colors"], # 複数色対応
            "image_url": p["image_url"],
            "product_url": p["product_url"]
        }
        batch.set(doc_ref, doc_data)
        index += 1

    try:
        batch.commit()
        print("スクレイピング結果をFirestoreに保存しました。")
    except Exception as e:
        print(f"Firestore保存中にエラーが発生しました: {e}")

except Exception as e:
    print(f"スクレイピング中にエラーが発生しました: {e}")
finally:
    driver.quit()
