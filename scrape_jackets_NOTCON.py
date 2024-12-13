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

# 対象ページURLおよびドライバパス
base_url = "https://not-conventional.com/products/list?category_id=505"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/600x600.png?text=No+Image"
store_id = "NOT_CONVENTIONAL_Kyoto"
category_id = "outerwear"

# ブラウザ起動とHTML取得
driver = webdriver.Chrome(service=service)
driver.get(base_url)
time.sleep(5)  # 必要に応じて調整
html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, 'html.parser')

# 商品リスト抽出
product_items = soup.select("ul.ec-shelfGrid li.ec-shelfGrid__item")

products_data = []
for item in product_items:
    a_tag = item.find("a", href=True)
    if not a_tag:
        continue

    product_url = a_tag['href']
    product_name_tag = item.find("p", class_="ec-shelfGrid__item-name")
    product_price_tag = item.find("p", class_="ec-shelfGrid__item-price")
    product_img_tag = item.find("div", class_="ec-shelfGrid__item-image").find("img")

    product_name = product_name_tag.get_text(strip=True) if product_name_tag else "No Name"
    product_price_text = product_price_tag.get_text(strip=True) if product_price_tag else "0"
    
    # 価格抽出(例 "￥44,000 tax in")
    price_match = re.search(r"￥([\d,]+)", product_price_text)
    product_price = 0
    if price_match:
        product_price = int(price_match.group(1).replace(",", ""))

    product_image_url = product_img_tag['src'] if product_img_tag else fallback_image_url
    if product_image_url.startswith("/"):
        product_image_url = "https://not-conventional.com" + product_image_url

    # 商品ID抽出 (例: https://not-conventional.com/products/detail/1684572 -> 1684572)
    product_id_match = re.search(r"/detail/(\d+)", product_url)
    product_id = None
    if product_id_match:
        product_id = product_id_match.group(1)

    products_data.append({
        "product_id": product_id,
        "product_name": product_name,
        "base_price": product_price,  
        "image_url": product_image_url,
        "link": product_url
    })

# eccube.productsClassCategories抽出
script_tags = soup.find_all("script")
eccube_data = None
for s in script_tags:
    if s.string and "eccube.productsClassCategories" in s.string:
        match = re.search(r"eccube\.productsClassCategories\s*=\s*(\{.*?\});", s.string, re.DOTALL)
        if match:
            json_str = match.group(1)
            json_str = json_str.rstrip(';')
            eccube_data = json.loads(json_str)
            break

if eccube_data is None:
    print("eccube.productsClassCategoriesの取得に失敗しました。")
    exit()

final_variants = []

# eccube_dataを用いてvariants抽出
for p in products_data:
    pid = p["product_id"]
    if pid not in eccube_data:
        # バリアント情報なし商品
        final_variants.append({
            "product_id": pid,
            "product_name": p["product_name"],
            "price": p["base_price"],
            "category_id": category_id,
            "store_id": store_id,
            "color": "No Color",  # カラー情報がない場合固定
            "size": None,
            "image_url": p["image_url"]
        })
        continue

    product_variants = eccube_data[pid]

    # product_variantsから実バリアントを抽出
    # 通常は __unselected や #キーがあり、その中の"#数字"が実際のバリアント
    found_variant = False
    for key_level1, val_level1 in product_variants.items():
        if not isinstance(val_level1, dict):
            continue
        for key_level2, val_level2 in val_level1.items():
            if not key_level2.startswith("#"):
                continue
            # バリアント情報取得
            variant_info = val_level2
            variant_size = variant_info.get("name", None)
            variant_price_str = variant_info.get("price01_inc_tax", "0")
            variant_price = 0
            try:
                variant_price = int(variant_price_str.replace(",", ""))
            except:
                pass

            final_variants.append({
                "product_id": pid,
                "product_name": p["product_name"],
                "price": variant_price if variant_price > 0 else p["base_price"],
                "category_id": category_id,
                "store_id": store_id,
                "color": "No Color",
                "size": variant_size if variant_size != "選択してください" else None,
                "image_url": p["image_url"]
            })
            found_variant = True

    # バリアントが一つも見つからなかった場合にも対応（理論上は上記で全て拾えるはず）
    if not found_variant:
        final_variants.append({
            "product_id": pid,
            "product_name": p["product_name"],
            "price": p["base_price"],
            "category_id": category_id,
            "store_id": store_id,
            "color": "No Color",
            "size": None,
            "image_url": p["image_url"]
        })

# 同一商品・同一カラーでまとめて、sizesに統合する処理
grouped_by_color = defaultdict(lambda: {
    "product_name": None,
    "price": None,
    "category_id": None,
    "store_id": None,
    "color": None,
    "image_url": None,
    "sizes": set()
})

for v in final_variants:
    key = (v["product_id"], v["color"])
    pdata = grouped_by_color[key]

    if pdata["product_name"] is None:
        pdata["product_name"] = v["product_name"]
    if pdata["price"] is None:
        pdata["price"] = v["price"]
    if pdata["category_id"] is None:
        pdata["category_id"] = v["category_id"]
    if pdata["store_id"] is None:
        pdata["store_id"] = v["store_id"]
    if pdata["color"] is None:
        pdata["color"] = v["color"]
    if pdata["image_url"] is None:
        pdata["image_url"] = v["image_url"]

    if v["size"]:
        pdata["sizes"].add(v["size"])

batch = db.batch()
for (pid, color), pdata in grouped_by_color.items():
    sizes_list = list(pdata["sizes"])
    safe_pid = str(pid).replace("/", "_")
    safe_color = str(color).replace("/", "_")
    doc_id = f"{safe_pid}_{safe_color}"

    doc_ref = db.collection("stores").document(pdata["store_id"]).collection("items").document(doc_id)
    doc_data = {
        "product_name": pdata["product_name"],
        "price": pdata["price"],
        "category_id": pdata["category_id"],
        "store_id": pdata["store_id"],
        "color": pdata["color"],
        "sizes": sizes_list,
        "image_url": pdata["image_url"]
    }
    batch.set(doc_ref, doc_data)

try:
    batch.commit()
    print("Firestoreへの保存が完了しました(重複なし)。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
