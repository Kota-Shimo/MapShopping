import firebase_admin
from firebase_admin import credentials, firestore

# Firebaseの初期化
if not firebase_admin._apps:  # 初期化済みか確認
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 店舗データ
stores = [
    {
        "id": "store_001",
        "name": "HUF Tokyo",
        "address": "Shibuya, Tokyo",
        "latitude": 35.6895,
        "longitude": 139.6917
    },
    {
        "id": "store_002",
        "name": "HUF Kyoto",
        "address": "Kyoto, Japan",
        "latitude": 35.0116,
        "longitude": 135.7681
    }
]

# Firestoreに店舗データを保存
for store in stores:
    doc_ref = db.collection("stores").document(store["id"])
    doc_ref.set({
        "name": store["name"],
        "address": store["address"],
        "latitude": store["latitude"],
        "longitude": store["longitude"]
    })

print("店舗データを保存しました！")
