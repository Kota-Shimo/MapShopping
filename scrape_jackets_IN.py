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
# ★ ここからFirebase初期化処理 ★
# =============================================
# Firebase初期化(既に初期化済みでなければ)
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# =============================================
# ★ スクレイピング対象URLと設定 ★
# =============================================
base_url = "https://store.in-net.gr.jp/category/OUTER_M/"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

fallback_image_url = "https://via.placeholder.com/100?text=No+Image"
store_id = "印_裏寺本店_セレクトショップ"
category_id = "outerwear"

# =============================================
# ★ 今回のサイト構造に合わせた関数例 ★
# =============================================
def get_soup(driver):
    # ページのHTMLを取得して、BeautifulSoupオブジェクトを返す
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def parse_products_from_soup(soup):
    """
    商品一覧が格納されている部分を解析する関数。
    今回の商品一覧は #itemListSimple 内の div.box が各商品。
    box内部構造：
    <div class="box">
      <div>
        <a href="商品個別URL" ...>
          <div class="item_swiper_container ...">
            <div class="hover_area ...">
              <span class="origin_image active swiper-slide">
                <span class="img_box">
                  <img src="..." alt="商品名" ...>
                </span>
              </span>
            </div>
          </div>
          <div class="text">
            <h4 class="brand">BRAND名</h4>
            <h3>商品名</h3>
            <div class="price">
              <div>
                <div>
                  <p class="price_en">¥XX,XXX円</p>
                </div>
              </div>
            </div>
          </div>
        </a>
      </div>
    </div>
    """
    products_data = []
    product_boxes = soup.select("#itemListSimple .box")
    for pb in product_boxes:
        # 商品詳細ページURL取得
        link_tag = pb.select_one("a[href]")
        if not link_tag:
            continue
        product_url = urllib.parse.urljoin(base_url, link_tag.get("href"))
        
        # 商品名
        name_tag = pb.select_one("h3")
        product_name = name_tag.get_text(strip=True) if name_tag else "No Name"
        
        # ブランド名
        brand_tag = pb.select_one("h4.brand")
        brand_name = brand_tag.get_text(strip=True) if brand_tag else ""
        
        # 価格(¥記号や円を除去して数値化が望ましい)
        price_tag = pb.select_one("p.price_en")
        price_text = price_tag.get_text(strip=True) if price_tag else "0"
        # "¥20,900円"などの形なので、不要文字を除去
        price_text_clean = re.sub(r"[¥,円]", "", price_text)
        try:
            price = float(price_text_clean)
        except:
            price = 0.0
        
        # 画像URL
        img_tag = pb.select_one(".img_box img")
        if img_tag:
            img_url = img_tag.get("src")
            if img_url and img_url.startswith("/"):
                # 相対パスの可能性を考慮してbase_urlで補完
                img_url = urllib.parse.urljoin(base_url, img_url)
        else:
            img_url = fallback_image_url
        
        # データを格納
        products_data.append({
            "product_name": product_name,
            "brand_name": brand_name,
            "price": price,
            "image_url": img_url,
            "product_url": product_url,
            "category_id": category_id,
            "store_id": store_id
        })
    return products_data

def get_next_page_url(soup):
    """
    ページ下部のページネーションから、次のページのURLを取得する関数。
    ページネーション例:
    <div class="pagelink">
      <span class="next"><a href="https://store.in-net.gr.jp/category/OUTER_M/?...&next_page=2"></a></span>
    </div>
    ここから次ページへのリンクを取得。
    """
    next_link = soup.select_one(".pagelink .next a")
    if next_link:
        next_url = next_link.get("href")
        if next_url:
            return urllib.parse.urljoin(base_url, next_url)
    return None

# =============================================
# ★ スクレイピング処理メイン ★
# =============================================
all_products = []
try:
    driver = webdriver.Chrome(service=service)
    current_url = base_url
    
    while True:
        driver.get(current_url)
        time.sleep(3)  # ページ読み込み待機。必要に応じて調整
        soup = get_soup(driver)
        
        products_on_page = parse_products_from_soup(soup)
        if not products_on_page:
            # 商品がない、または取得できない場合は終了
            break
        
        all_products.extend(products_on_page)
        
        # 次ページがあるか確認
        next_page_url = get_next_page_url(soup)
        if not next_page_url:
            # 次ページがなければ終了
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
# ★ Firestoreへ保存（元の処理に近い形） ★
# =============================================
batch = db.batch()
index = 0

for product in all_products:
    # ドキュメントID生成例：商品名+ブランド名をIDに使えないのでURLなどを利用する、またはインデックスで代替
    # ここではproduct_nameとbrand_nameを連結し、スラッシュなどをアンダーバーに変換
    doc_id = re.sub(r"[/\\ ]+", "_", product["product_name"] + "_" + product["brand_name"] + "_" + str(index))
    
    doc_ref = db.collection("stores").document(product["store_id"]).collection("items").document(doc_id)
    doc_data = {
        "product_name": product["product_name"],
        "brand_name": product["brand_name"],
        "price": product["price"],
        "category_id": product["category_id"],
        "store_id": product["store_id"],
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
