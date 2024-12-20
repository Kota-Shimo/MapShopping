import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")  # サービスアカウントキーへのパス
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 店舗情報の定義
stores_data = {
    "KAPITAL KYOTO": {
        "address": "〒604-8066 京都府京都市中京区六角下ル伊勢屋町352",
        "latitude": 35.006973379821794,   # 仮の値
        "longitude": 135.7662933810575,  # 仮の値
        "name": "KAPITAL KYOTO",
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
        "contact": "075-229-3255"
    },
    "FASCINATE KYOTO": {
        "address": "〒604-8044 京都府京都市中京区大日町416-5 御幸町スクエアDECO III 1F",
        "latitude": 35.0044600307616,   # 仮の値
        "longitude": 135.7661860927011,  # 仮の値
        "name": "FASCINATE KYOTO",
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
        "contact": "075-708-3919"
    },
}

# データベースへの書き込み
for store_id, store_info in stores_data.items():
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")
