import json
import firebase_admin
from firebase_admin import credentials, firestore
import re
from bs4 import BeautifulSoup
import requests
from collections import defaultdict

# =========================================
# 1. Firebase初期化
# =========================================
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# =========================================
# 2. スクレイピング対象URLや設定
# =========================================
target_url = "https://www.prophet-kyoto.com/category/item/itemgenre/outer/down/"

store_id = "PROOF"     # 任意のstore_id
category_id = "down jacket"  # カテゴリID（任意）

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"

# =========================================
# 3. HTML取得と解析
# =========================================
try:
    response = requests.get(target_url)
    response.raise_for_status()
    html = response.text
except Exception as e:
    print(f"ページ取得中にエラーが発生しました: {e}")
    exit()

soup = BeautifulSoup(html, 'html.parser')

# =========================================
# 4. 商品リスト解析
#    商品要素は <article class="post-item"> が商品カードとして並んでいる
# =========================================
product_articles = soup.find_all('article', class_='post-item')

final_items = []

for article in product_articles:
    # 商品名取得
    name_tag = article.find('h3', class_='card-title')
    product_name = name_tag.get_text(strip=True) if name_tag else "No Name"

    # ブランド名取得
    brand_tag = article.find('div', class_='item-list-brand')
    brand = brand_tag.find('a').get_text(strip=True) if brand_tag and brand_tag.find('a') else "No Brand"

    # 価格取得
    # クラス指定はスペース区切りのまま文字列で指定する
    price_div = article.find('div', class_='card-text item-price')
    price_text = price_div.get_text(strip=True) if price_div else ""

    # "SOLD OUT"チェック
    if "SOLD OUT" in price_text.upper():
        final_price = 0
    else:
        # ¥マーク以降の数字を抽出
        price_match = re.findall(r'¥([\d,]+)', price_text)
        if price_match:
            # 複数価格あれば最後（セール後価格）を採用
            final_price = int(price_match[-1].replace(',', ''))
        else:
            # 売り切れでもなく価格もない場合は0とする
            final_price = 0

    # 画像URL取得
    img_div = article.find('div', class_='card-image')
    img_tag = img_div.find('img') if img_div else None
    image_url = img_tag.get('src') if (img_tag and img_tag.has_attr('src')) else fallback_image_url

    # 商品詳細URL取得
    link_div = article.find('div', class_='card-imag-top')
    link_tag = link_div.find('a') if link_div else None
    product_url = link_tag.get('href') if link_tag else None

    # product_id生成
    product_id = "unknown_id"
    if product_url:
        match_id = re.search(r'/item/(\d+)/', product_url)
        if match_id:
            product_id = match_id.group(1)
        else:
            # 数字がなければURLをsafeなIDに変換
            product_id = re.sub(r'[^\w]+', '_', product_url)

    # カラー・サイズ情報がない場合は"N/A"
    color = "N/A"
    sizes = []

    final_items.append({
        "product_id": product_id,
        "product_name": product_name,
        "brand": brand,
        "price": final_price,
        "category_id": category_id,
        "store_id": store_id,
        "color": color,
        "sizes": sizes,
        "image_url": image_url,
        "product_url": product_url
    })

print(f"合計{len(final_items)}件の商品を取得しました。")

# =========================================
# 5. Firebase Firestoreへの保存
# =========================================
batch = db.batch()
for item in final_items:
    # doc_id内に'/'や'\\'などがあれば置換
    doc_id = f"{item['product_id']}_{item['color']}"
    doc_id = doc_id.replace('/', '_').replace('\\', '_')
    
    doc_ref = db.collection("stores").document(item["store_id"]).collection("items").document(doc_id)
    doc_data = {
        "product_name": item["product_name"],
        "brand": item["brand"],
        "price": item["price"],
        "category_id": item["category_id"],
        "store_id": item["store_id"],
        "color": item["color"],
        "sizes": item["sizes"],
        "image_url": item["image_url"],
        "product_url": item["product_url"]
    }
    batch.set(doc_ref, doc_data)

try:
    batch.commit()
    print("Firestoreへの保存が完了しました。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
