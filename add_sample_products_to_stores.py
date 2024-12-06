import firebase_admin
from firebase_admin import credentials, firestore

# Firebaseの初期化
if not firebase_admin._apps:  # 初期化済みか確認
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# サンプル商品データ（簡略化）
sample_products = [
    {"variant_name": "サンプル商品1", "price": 1000, "tags": ["sample", "jacket", "product1"]},
    {"variant_name": "サンプル商品2", "price": 2000, "tags": ["sample", "jacket", "product2"]},
    {"variant_name": "サンプル商品3", "price": 3000, "tags": ["sample", "jacket", "product3"]}
]

# 店舗IDリスト
store_ids = [
    "2gQimhkUzf2tU7Y9ZLas",
    "E5PUEvaXqE2VMzI1e3ZY",
    "R8T1NE6Bf7qC7Z7woeXG",
    "Vv9G8GV46RYfp6lNJmfK",
    "X2xdbejVdkfoVzv9O1TM",
    "fqBgbW53nwQRDUnAdPnQ"
]

# カテゴリIDを指定（例として 'jackets' を使用）
category_id = 'jackets'

# 各店舗に商品を登録
for store_id in store_ids:
    for product in sample_products:
        # Firestoreのパスを指定（stores/{store_id}/items に保存）
        doc_ref = db.collection("stores").document(store_id).collection("items").document()
        doc_ref.set({
            "variant_name": product["variant_name"],
            "price": product["price"],
            "tags": product["tags"],
            "store_id": store_id,      # 店舗IDを追加
            "category_id": category_id # カテゴリIDを追加
        })

print("すべての店舗にサンプル商品を保存しました！")
