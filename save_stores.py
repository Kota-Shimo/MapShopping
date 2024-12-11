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
        "address": "京都府京都市下京区麩屋町通高辻上る鍋屋町244-1",
        "latitude": 35.00054907726847,
        "longitude": 135.76562278043016,
        "name": "lloomm",
        "hours": {
            "Monday": "13:00 - 19:00",
            "Tuesday": "13:00 - 19:00",
            "Wednesday": "13:00 - 19:00",
            "Thursday": "13:00 - 19:00",
            "Friday": "13:00 - 19:00",
            "Saturday": "13:00 - 19:00",
            "Sunday": "13:00 - 19:00"
        },
        "closed": [],
        "contact": "075-354-0373"
    },
    "E5PUEvaXqE2VMzI1e3ZY": {
        "address": "京都府京都市東山区二町目50",
        "latitude": 35.009213860879825,
        "longitude": 135.77530175159507,
        "name": "RADLOSTEL",
        "hours": {
            "Monday": "12:00 - 19:00",
            "Tuesday": "12:00 - 19:00",
            "Wednesday": "12:00 - 19:00",
            "Thursday": "12:00 - 19:00",
            "Friday": "12:00 - 19:00",
            "Saturday": "12:00 - 19:00",
            "Sunday": "12:00 - 19:00"
        },
        "closed": [],
        "contact": "080-4563-7032"
    },
    "R8T1NE6Bf7qC7Z7woeXG": {
        "address": "京都市中京区船屋町387 第2四寅ビル1F",
        "latitude": 35.00551736819462,
        "longitude": 135.76616370741652,
        "name": "ATTEMPT Kyoto",
        "hours": {
            "Monday": "11:00 - 19:00",
            "Tuesday": "11:00 - 19:00",
            "Wednesday": "定休日",
            "Thursday": "11:00 - 19:00",
            "Friday": "11:00 - 20:00",
            "Saturday": "12:00 - 20:00",
            "Sunday": "12:00 - 18:00"
        },
        "closed": ["Wednesday"],
        "contact": "075-366-4330"
    },
    "Vv9G8GV46RYfp6lNJmfK": {
        "address": "京都府京都市左京区聖護院東町7",
        "latitude": 35.00642050292674,
        "longitude": 135.76511808043043,
        "name": "601",
        "hours": {
            "Monday": "10:00 - 18:00",
            "Tuesday": "10:00 - 18:00",
            "Wednesday": "10:00 - 18:00",
            "Thursday": "10:00 - 18:00",
            "Friday": "10:00 - 18:00",
            "Saturday": "11:00 - 19:00",
            "Sunday": "11:00 - 19:00"
        },
        "closed": [],
        "contact": "075-771-0106"
    },
    "X2xdbejVdkfoVzv9O1TM": {
        "address": "京都市中京区堺町通錦上る菊屋町519",
        "latitude": 35.0085980502084,
        "longitude": 135.7473479246086,
        "name": "BELLEGANZA",
        "hours": {
            "Monday": "11:00 - 20:00",
            "Tuesday": "11:00 - 20:00",
            "Wednesday": "11:00 - 20:00",
            "Thursday": "11:00 - 20:00",
            "Friday": "11:00 - 20:00",
            "Saturday": "11:00 - 20:00",
            "Sunday": "11:00 - 20:00"
        },
        "closed": [],
        "contact": "075-211-1199"
    },
    "fqBgbW53nwQRDUnAdPnQ": {
        "address": "京都府京都市上京区出水通堀川東入る出水町249-1",
        "latitude": 35.019925981430134,
        "longitude": 135.76919740346833,
        "name": "hillside",
        "hours": {
            "Monday": "11:00 - 19:00",
            "Tuesday": "11:00 - 19:00",
            "Wednesday": "11:00 - 19:00",
            "Thursday": "11:00 - 19:00",
            "Friday": "11:00 - 19:00",
            "Saturday": "11:00 - 19:00",
            "Sunday": "11:00 - 19:00"
        },
        "closed": [],
        "contact": "075-414-2050"
    },
    "store_001": {
        "address": "東京都渋谷区神宮前4丁目25-10",
        "latitude": 35.6895,
        "longitude": 139.6917,
        "name": "HUF Tokyo",
        "hours": {
            "Monday": "11:00 - 20:00",
            "Tuesday": "11:00 - 20:00",
            "Wednesday": "11:00 - 20:00",
            "Thursday": "11:00 - 20:00",
            "Friday": "11:00 - 20:00",
            "Saturday": "11:00 - 20:00",
            "Sunday": "11:00 - 20:00"
        },
        "closed": [],
        "contact": "03-5778-8126"
    },
    "store_002": {
        "address": "京都府京都市中京区寺町通四条上る中之町559",
        "latitude": 35.006894413711485,
        "longitude": 135.76715794306384,
        "name": "HUF Kyoto",
        "hours": {
            "Monday": "11:00 - 20:00",
            "Tuesday": "11:00 - 20:00",
            "Wednesday": "11:00 - 20:00",
            "Thursday": "11:00 - 20:00",
            "Friday": "11:00 - 20:00",
            "Saturday": "11:00 - 20:00",
            "Sunday": "11:00 - 20:00"
        },
        "closed": [],
        "contact": "075-256-8156"
    }
}


# データベースへの書き込み
for store_id, store_info in stores_data.items():
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")
