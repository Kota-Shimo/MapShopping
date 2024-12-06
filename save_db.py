import firebase_admin
from firebase_admin import credentials, firestore
import json

# Firebaseの初期化
if not firebase_admin._apps:  # 初期化済みか確認
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()

# 保存先ファイル
output_file = "firestore_backup.json"

# データを抽出する関数
def export_firestore_data():
    data = {}
    # 例: 'stores'コレクションから全てのデータを取得
    stores_ref = db.collection('stores')
    docs = stores_ref.get()

    for doc in docs:
        data[doc.id] = doc.to_dict()  # ドキュメントIDをキーにして保存

    # JSONファイルとして保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"データを {output_file} に保存しました。")

export_firestore_data()
