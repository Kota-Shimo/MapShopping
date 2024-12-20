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

# ターゲットURL
base_url = "https://www.descendant-kyoto.jp/collections/shirt"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

store_id = "DESCENDANT_KYOTO"
category_id = "shirts"

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
    """
    product_nameとcolorを小文字にして、products_from_html_all内のnameにcolorとproduct_nameを含む画像を探す。
    1. color+product_name両方含む
    2. product_nameのみ含む
    """
    p_lower = product_name.lower().strip()
    c_lower = color.lower().strip()

    # color+product_name含むalt
    color_candidates = []
    for hp in products:
        hname = hp["name"].lower()
        if c_lower in hname and p_lower in hname:
            color_candidates.append(hp["image_url"])
    if color_candidates:
        return color_candidates[0]

    # product_nameのみ含む
    name_candidates = []
    for hp in products:
        hname = hp["name"].lower()
        if p_lower in hname:
            name_candidates.append(hp["image_url"])
    if name_candidates:
        return name_candidates[0]

    return None

def adjust_image_url(img_url):
    if img_url and "&width=" in img_url:
        img_url = re.sub(r"&width=\d+", "&width=1024", img_url)
    return img_url

final_variants = []
products_from_html_all = []

try:
    driver = webdriver.Chrome(service=service)
    page_url = base_url
    driver.get(page_url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    product_divs = soup.find_all('div', class_='product-card')

    if product_divs:
        products_from_html = []
        for product_div in product_divs:
            img_tag = product_div.find('img', class_='product-card__img')
            product_name_tag = product_div.find('h2', class_='product-card__title')
            if not img_tag or not product_name_tag:
                continue
            product_name_html = product_name_tag.get_text(strip=True)
            product_image_url = img_tag.get('src')
            if product_image_url and product_image_url.startswith('//'):
                product_image_url = 'https:' + product_image_url
            if product_image_url:
                products_from_html.append({
                    "name": product_name_html,
                    "image_url": product_image_url
                })
        products_from_html_all.extend(products_from_html)

        # scriptタグからmetaデータ抽出
        script_tag = soup.find('script', text=re.compile(r"var meta ="))
        if script_tag:
            script_content = script_tag.string.strip()

            json_data_match = re.search(r"var meta = (.*?);", script_content)
            if json_data_match:
                json_data = json_data_match.group(1)
                data = json.loads(json_data)
                page_products = data.get("products", [])
                if page_products:
                    for product_json in page_products:
                        product_id = product_json.get("id")
                        title = product_json.get("title", "").strip()
                        images = product_json.get("images", [])
                        image_map = {}
                        images_extended = []
                        for img_obj in images:
                            img_id = img_obj.get("id")
                            img_src = img_obj.get("src")
                            img_alt = img_obj.get("alt", "")
                            if img_id and img_src:
                                image_map[img_id] = img_src
                                images_extended.append({
                                    "id": img_id,
                                    "src": img_src,
                                    "alt": img_alt if img_alt else ""
                                })

                        variants = product_json.get("variants", [])
                        if not variants:
                            continue

                        if not title and variants:
                            title = extract_product_base_name(variants[0]["name"]) or "No Name"

                        for variant in variants:
                            variant_name = variant["name"]
                            variant_price = variant["price"] / 100
                            parts = variant_name.split('/')
                            size = None
                            base_name = variant_name
                            if len(parts) > 1:
                                size = parts[-1].strip()
                                base_name = '/'.join(parts[:-1]).strip()

                            base_parts = base_name.rsplit(' - ', 1)
                            color = "No Color"
                            if len(base_parts) > 1:
                                color = base_parts[-1].strip()

                            variant_image_id = variant.get("image_id")
                            variant_featured_image = None
                            if variant.get("featured_image") and variant["featured_image"].get("src"):
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
                                "image_map": image_map,
                                "images_extended": images_extended
                            })

except Exception as e:
    print(f"ページ取得中にエラーが発生しました: {e}")
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
    """
    カラー別の画像を可能な限り取得する。
    優先度:
    1. variantごとのfeatured_image（最も信頼度が高い）
    2. image_idで紐づく固有画像
    3. images_extended.alt にcolorが含まれる画像
    4. strict_image_search_by_color

    見つからなければNoneを返す(保存スキップ)
    """
    color = pdata["color"].strip().lower()
    if color == "no color":
        color = ""

    # 1. variantごとのfeatured_image優先
    for var in pdata["variants_data"]:
        if var["featured_image"]:
            img_url = adjust_image_url(var["featured_image"])
            if img_url:
                return img_url

    # 2. image_idマッチ
    for var in pdata["variants_data"]:
        if var["image_id"] and var["image_id"] in var["image_map"]:
            img_url = adjust_image_url(var["image_map"][var["image_id"]])
            if img_url:
                return img_url

    # 3. images_extendedからaltテキストマッチ
    # colorが空でなければ、colorを含むaltを探す
    if color:
        for var in pdata["variants_data"]:
            for img_info in var["images_extended"]:
                alt_text = img_info["alt"].lower().strip()
                if color in alt_text:
                    img_url = adjust_image_url(img_info["src"])
                    if img_url:
                        return img_url
    else:
        # no colorの場合は最初の画像
        for var in pdata["variants_data"]:
            if var["images_extended"]:
                img_url = adjust_image_url(var["images_extended"][0]["src"])
                if img_url:
                    return img_url

    # 4. strict_image_search_by_color
    img = strict_image_search_by_color(pdata["product_name"], pdata["color"], products_from_html_all)
    if img:
        img = adjust_image_url(img)
        if img:
            return img

    return None

batch = db.batch()
index = 0
for (pid, color), pdata in grouped_by_color.items():
    img = get_color_image(pdata)
    # 画像が取得できないならスキップ
    if img is None:
        continue

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
    print("保存が完了しました。")
except Exception as e:
    print(f"Firestore保存中にエラーが発生しました: {e}")
