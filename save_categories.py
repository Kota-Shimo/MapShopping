import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")  # サービスアカウントキーへのパス
    firebase_admin.initialize_app(cred)

db = firestore.client()

# カテゴリ一覧（Pythonの辞書として定義）
categories = [
    { "id": "outerwear", "name": "アウターウェア" },
    { "id": "tops", "name": "トップス" },
    { "id": "bottoms", "name": "ボトムス" },
    { "id": "jackets", "name": "ジャケット" },
    { "id": "shirts", "name": "シャツ" },
    { "id": "pants", "name": "パンツ" },
    { "id": "sweatshirts", "name": "スウェットシャツ" },
    { "id": "t-shirts", "name": "Tシャツ" },
    { "id": "denim", "name": "デニム" },
    { "id": "accessories", "name": "アクセサリー" }
]

# データベースへの書き込み
for cat in categories:
    doc_ref = db.collection("categories").document(cat["id"])
    doc_ref.set({
        "name": cat["name"]
    })
    print(f"カテゴリ '{cat['name']}' (ID: {cat['id']}) を登録しました。")
