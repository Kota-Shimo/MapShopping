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

base_url = "https://601-store.com/collections/coat"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/600x600.png?text=No+Image"
store_id = "Vv9G8GV46RYfp6lNJmfK"
category_id = "outerwear"

def extract_product_base_name(variant_name):
    parts = variant_name.split('/')
    if len(parts) > 1:
        base_name = '/'.join(parts[:-1]).strip()
    else:
        base_name = variant_name.strip()

    base_parts = base_name.rsplit(' - ', 1)
    if len(base_parts) > 1:
        product_base = base_parts[0].strip()
    else:
        product_base = base_name.strip()
    return product_base

def strict_image_search_by_color(product_name, color, products):
    p_lower = product_name.lower()
    c_lower = color.lower()

    if c_lower != "no color" and c_lower:
        color_candidates = []
        for hp in products:
            hname = hp["name"].lower()
            if c_lower in hname and p_lower in hname:
                color_candidates.append(hp["image_url"])
        if color_candidates:
            return color_candidates[0]

    # product_nameのみ
    name_candidates = []
    for hp in products:
        hname = hp["name"].lower()
        if p_lower in hname:
            name_candidates.append(hp["image_url"])
    if name_candidates:
        return name_candidates[0]

    return None

final_variants = []
products_from_html_all = []

try:
    driver = webdriver.Chrome(service=service)
    page = 1
    seen_variants = set()  # 重複防止用セット

    while True:
        page_url = f"{base_url}?page={page}"
        driver.get(page_url)
        time.sleep(5)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        product_divs = soup.find_all('div', class_='card-wrapper')

        if len(product_divs) == 0:
            break

        products_from_html = []
        for product_div in product_divs:
            img_tag = product_div.find('img')
            if not img_tag:
                continue
            product_name_html = img_tag.get('alt', 'No Name').strip()
            
            # 画像URL取得ロジック改善
            product_image_url = img_tag.get('src') or img_tag.get('data-src')
            if not product_image_url:
                # srcやdata-srcがない場合、srcsetから取得
                srcset = img_tag.get('srcset')
                if srcset:
                    first_src = srcset.split()[0]
                    product_image_url = first_src

            if product_image_url and product_image_url.startswith('//'):
                product_image_url = 'https:' + product_image_url
            if product_image_url:
                products_from_html.append({
                    "name": product_name_html,
                    "image_url": product_image_url
                })
        products_from_html_all.extend(products_from_html)

        # ページ内にShopifyAnalytics.metaが含まれたscriptがあるかチェック
        script_tag = soup.find('script', string=lambda x: x and "ShopifyAnalytics.meta" in x)
        if not script_tag:
            break
        script_content = script_tag.string.strip()
        json_data_match = re.search(r"var meta = (.*);", script_content)
        if not json_data_match:
            break

        json_data = json_data_match.group(1)
        data = json.loads(json_data)
        page_products = data.get("products", [])
        if not page_products:
            break

        for product_json in page_products:
            product_id = product_json.get("id")
            title = product_json.get("title", "").strip()

            images = product_json.get("images", [])
            image_map = {}
            for img_obj in images:
                if "id" in img_obj and "src" in img_obj:
                    image_map[img_obj["id"]] = img_obj["src"]

            variants = product_json.get("variants", [])
            if not variants:
                continue

            if not title and variants:
                title = extract_product_base_name(variants[0]["name"]) or "No Name"

            for variant in variants:
                variant_id = variant["id"]
                variant_name = variant["name"]
                variant_price = variant["price"] / 100

                if variant_id in seen_variants:
                    continue
                seen_variants.add(variant_id)

                parts = variant_name.split('/')
                # colorとsize抽出ロジック修正
                # 例: "FUMIKA_UCHIDA / SPLASHED PATTERN ZIP-UP BLOUSON / BROWN - 38"
                # 最後の要素が "BROWN - 38"
                # それを' - 'で分けてcolorとsizeを取得
                if len(parts) > 1:
                    suffix = parts[-1].strip()  # "BROWN - 38" のような形式
                    prefix = '/'.join(parts[:-1]).strip()
                else:
                    suffix = parts[0].strip()
                    prefix = ""

                suffix_parts = suffix.split(' - ')
                if len(suffix_parts) == 2:
                    color = suffix_parts[0].strip()
                    size = suffix_parts[1].strip()
                else:
                    # カラーとサイズどちらかが取れない場合のフォールバック
                    # 例えばサイズがない、またはカラーサイズ分けがない場合
                    color = "No Color"
                    size = None

                if not title:
                    title = extract_product_base_name(prefix) or "No Name"

                variant_image_id = variant.get("image_id")
                variant_featured_image = None
                if "featured_image" in variant and variant["featured_image"] and "src" in variant["featured_image"]:
                    variant_featured_image = variant["featured_image"]["src"]

                final_variants.append({
                    "product_id": product_id,
                    "product_name": title,
                    "price": variant_price,
                    "category_id": category_id,
                    "store_id": store_id,
                    "color": color,
                    "size": size,
                    "image_id": variant_image_id,
                    "featured_image": variant_featured_image,
                    "image_map": image_map
                })
        page += 1

    print("全ページの商品取得が完了しました。")
except Exception as e:
    print(f"ページ取得中にエラーが発生しました: {e}")
    exit()
finally:
    driver.quit()

from collections import defaultdict
grouped_by_color = defaultdict(lambda: {
    "product_name": None,
    "price": None,
    "category_id": None,
    "store_id": None,
    "color": None,
    "sizes": set(),
    "variants_data": []
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

    if v["size"]:
        pdata["sizes"].add(v["size"])
    pdata["variants_data"].append(v)

def get_color_image(pdata):
    # 1. variantにimage_idがあればimage_map参照
    for var in pdata["variants_data"]:
        if var["image_id"] and var["image_id"] in var["image_map"]:
            img_url = var["image_map"][var["image_id"]]
            # widthパラメータを変更
            if img_url and "&width=" in img_url:
                img_url = re.sub(r"&width=\d+", "&width=1024", img_url)
            return img_url

    # 2. featured_imageあるvariant
    for var in pdata["variants_data"]:
        if var["featured_image"]:
            img_url = var["featured_image"]
            if img_url and "&width=" in img_url:
                img_url = re.sub(r"&width=\d+", "&width=1024", img_url)
            return img_url

    # 3. HTMLフォールバック(厳密)
    img = strict_image_search_by_color(pdata["product_name"], pdata["color"], products_from_html_all)
    if not img:
        # カラー指定で見つからない場合はカラー無視
        img = strict_image_search_by_color(pdata["product_name"], "", products_from_html_all)

    if not img:
        img = fallback_image_url
    else:
        # 幅パラメータ調整
        if "&width=" in img:
            img = re.sub(r"&width=\d+", "&width=1024", img)
    return img

batch = db.batch()
index = 0
for (pid, color), pdata in grouped_by_color.items():
    img = get_color_image(pdata)

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
        "sizes": list(pdata["sizes"]),
        "image_url": img
    }
    batch.set(doc_ref, doc_data)
    index += 1

try:
    batch.commit()
    print("幅パラメータを変更して高解像度画像URLを保存しました。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
