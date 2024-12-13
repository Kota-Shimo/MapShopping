import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")  # サービスアカウントキーへのパス
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 店舗情報の定義
stores_data = {
    "STUDIOUS_MENS_京都三条店": {
        "address": "〒604-8083 京都府京都市中京区中之町1番地 小川ビル1F・2F",
        "latitude": 35.00890447440106,
        "longitude": 135.76422226878702,
        "name": "STUDIOOUS MENS 京都三条店",
        "hours": {
            "Monday": "12:00 - 20:00",
            "Tuesday": "12:00 - 20:00",
            "Wednesday": "12:00 - 20:00",
            "Thursday": "12:00 - 20:00",
            "Friday": "12:00 - 20:00",
            "Saturday": "12:00 - 20:00",
            "Sunday": "12:00 - 20:00"
        },
        "closed": [],
        "contact": "075-708-7551"
    },
    "DESCENDANT_KYOTO": {
        "address": "〒604-8072 京都府京都市中京区八百屋町105-1",
        "latitude": 35.0074245503697,
        "longitude": 135.76607073810175,
        "name": "DESCENDANT KYOTO",
        "hours": {
            "Monday": "12:00 - 19:00",
            "Tuesday": "12:00 - 19:00",
            "Wednesday": "12:00 - 19:00",
            "Thursday": "12:00 - 19:00",
            "Friday": "12:00 - 19:00",
            "Saturday": "12:00 - 19:00",
            "Sunday": "12:00 - 19:00"
        },
        "closed": ["Wednesday"],
        "contact": "075-212-0002"
    },
    "印_裏寺本店_セレクトショップ": {
        "address": "〒604-8042 京都府京都市中京区新京極通四条上る中之町577-2",
        "latitude": 35.00741576261889,
        "longitude": 135.76600636508792,
        "name": "印 裏寺本店（セレクトショップ）",
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
        "contact": "075-254-6066"
    },
    "NOT_CONVENTIONAL_Kyoto": {
        "address": "〒604-8041 京都府京都市中京区裏寺町595-3",
        "latitude": 35.00555580054331,
        "longitude": 135.76703979577292,
        "name": "NOT CONVENTIONAL Kyoto",
        "hours": {
            "Monday": "12:00 - 20:00",
            "Tuesday": "12:00 - 20:00",
            "Wednesday": "12:00 - 20:00",
            "Thursday": "12:00 - 20:00",
            "Friday": "12:00 - 20:00",
            "Saturday": "12:00 - 20:00",
            "Sunday": "12:00 - 20:00"
        },
        "closed": [],
        "contact": "075-746-4411"
    }
}

# データベースへの書き込み
for store_id, store_info in stores_data.items():
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")
