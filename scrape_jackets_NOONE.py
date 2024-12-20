import json
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 例：knitカテゴリーのURL（商品が無い場合は別のカテゴリーやトップページ等を試してください）
base_url = "https://www.noone-shop.com/shop/knit/27"
driver_path = r"C:\Users\kotas\Downloads\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)

store_id = "NOONE"
category_id = "knit"

# スクレイピング開始
try:
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)
    time.sleep(5)  # ページ読み込み待ち（状況に応じて増減）

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # __BOOTSTRAP_STATE__を含むscriptタグ抽出
    script_tags = soup.find_all("script")
    bootstrap_script = None
    for script in script_tags:
        if "window.__BOOTSTRAP_STATE__" in script.text:
            bootstrap_script = script.text
            break

    if not bootstrap_script:
        print("BOOTSTRAP_STATEが見つかりません。終了します。")
        exit()

    # "window.__BOOTSTRAP_STATE__ = { ... };"からJSON部分を抽出
    json_str = bootstrap_script.split("window.__BOOTSTRAP_STATE__ = ", 1)[1].rsplit(";", 1)[0].strip()
    data = json.loads(json_str)

    # commerceLinks.products から商品情報取得を試みる
    products = data.get("commerceLinks", {}).get("products", {})

    if not products:
        print("productsが空です。該当ページに商品が存在しない可能性があります。")
        # 必要であれば、別のキーを探索する処理や他のカテゴリーURLを試してください。
    else:
        # products内に商品がある場合、その情報をFirestoreに保存
        batch = db.batch()
        index = 0

        # fallbackが必要なら用意
        fallback_image_url = "https://via.placeholder.com/100?text=No+Image"

        for pid, pinfo in products.items():
            product_name = pinfo.get("name", "No Name")
            product_price = pinfo.get("price", 0)
            # 画像URLなど他の情報のキーはdata全体を確認して特定する必要があります。
            # ここでは、例としてimage_urlキーがあると仮定
            product_image = pinfo.get("image_url", fallback_image_url)

            doc_id = str(pid)
            doc_ref = db.collection("stores").document(store_id).collection("items").document(doc_id)
            doc_data = {
                "product_name": product_name,
                "price": product_price,
                "category_id": category_id,
                "store_id": store_id,
                "image_url": product_image
            }
            batch.set(doc_ref, doc_data)
            index += 1

        try:
            batch.commit()
            print(f"{index}件の商品情報をFirestoreに保存しました。")
        except Exception as e:
            print(f"Firestore保存中にエラーが発生しました: {e}")

except Exception as e:
    print(f"エラーが発生しました: {e}")
finally:
    driver.quit()
