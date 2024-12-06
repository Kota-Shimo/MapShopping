import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")  # サービスアカウントキーへのパス
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ユーザーから提供された店舗情報（Pythonの辞書として定義）
stores_data = {
    "2gQimhkUzf2tU7Y9ZLas": {
        "address": "京都府京都市下京区麩屋町通高辻上ル鍋屋町244-1",
        "latitude": 35.00054907726847,
        "longitude": 135.76562278043016,
        "name": "lloomm"
    },
    "E5PUEvaXqE2VMzI1e3ZY": {
        "address": "京都府京都市東山区二町目50",
        "latitude": 35.009213860879825,
        "longitude": 135.77530175159507,
        "name": "RADLOSTEL"
    },
    "R8T1NE6Bf7qC7Z7woeXG": {
        "address": "京都市中京区船屋町387 第2四寅ビル1F",
        "latitude": 35.00551736819462,
        "longitude": 135.76616370741652,
        "name": "ATTEMPT Kyoto"
    },
    "Vv9G8GV46RYfp6lNJmfK": {
        "address": "京都市左京区聖護院東町7",
        "latitude": 35.00642050292674,
        "longitude": 135.76511808043043,
        "name": "601"
    },
    "X2xdbejVdkfoVzv9O1TM": {
        "address": "京都市中京区堺町通錦上ル菊屋町519",
        "latitude": 35.0085980502084,
        "longitude": 135.7473479246086,
        "name": "BELLEGANZA"
    },
    "fqBgbW53nwQRDUnAdPnQ": {
        "address": "京都市上京区出水通り堀川東入る出水町249-1",
        "latitude": 35.019925981430134,
        "longitude": 135.76919740346833,
        "name": "hillside"
    },
    "store_001": {
        "latitude": 35.6895,
        "address": "Shibuya, Tokyo",
        "longitude": 139.6917,
        "name": "HUF Tokyo"
    },
    "store_002": {
        "address": "Kyoto, Japan",
        "latitude": 35.006894413711485,
        "longitude": 135.76715794306384,
        "name": "HUF Kyoto"
    }
}

# データベースへの書き込み
for store_id, store_info in stores_data.items():
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")
