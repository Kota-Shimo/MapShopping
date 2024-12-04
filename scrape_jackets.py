import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import re

# Firebaseの初期化
if not firebase_admin._apps:  # 初期化済みか確認
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# URLの設定
url = "https://www.hufworldwide.jp/collections/jackets"

# データを取得
try:
    response = requests.get(url, timeout=10)  # タイムアウトを設定
    response.raise_for_status()  # ステータスコードを確認
    print("ページの取得に成功しました！")
    html = response.text
except requests.exceptions.RequestException as e:
    print(f"ページの取得中にエラーが発生しました: {e}")
    exit()

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html, 'html.parser')
script_tag = soup.find('script', string=lambda x: x and "ShopifyAnalytics.meta" in x)

if not script_tag:
    print("適切なスクリプトタグが見つかりませんでした。")
    exit()

# JSONデータを抽出して解析
try:
    script_content = script_tag.string.strip()
    json_data_match = re.search(r"var meta = (.*);", script_content)
    if json_data_match:
        json_data = json_data_match.group(1)
        data = json.loads(json_data)
    else:
        print("JSONデータの抽出に失敗しました。")
        exit()
except Exception as e:
    print(f"JSONデータの解析中にエラーが発生しました: {e}")
    exit()

# 商品データをFirestoreに保存
products = data.get("products", [])
batch = db.batch()  # バッチ処理の開始

# store_id を手動で設定する
store_id = "store_002"  # 店舗IDを指定（例: store_002）

for product in products:
    variants = product["variants"]

    for variant in variants:
        variant_name = variant["name"]
        variant_price = variant["price"] / 100  # 価格を100で割って正規の金額に変換

        # キーワードのリストを作成（variant_nameのみを使用）
        tags = re.findall(r'\b\w+\b', variant_name.lower())

        print(f"バリエーション: {variant_name}, 価格: ¥{variant_price}")

        # Firestoreにカテゴリごとに保存
        doc_ref = db.collection("categories").document("jackets").collection("items").document(str(variant["id"]))
        batch.set(doc_ref, {
            "variant_name": variant_name,
            "price": variant_price,
            "store_id": store_id,
            "tags": tags  # キーワードを追加
        })

# バッチ処理のコミット（保存実行）
try:
    batch.commit()
    print("すべてのデータを保存しました。")
except Exception as e:
    print(f"バッチ処理中にエラーが発生しました: {e}")
