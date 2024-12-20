import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")  # サービスアカウントキーへのパス
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 店舗情報の定義
stores_data = {
    "NOONE": {
        "address": "〒604-8062 京都府京都市中京区蛸屋町１５６",
        "latitude": 35.00656914007891, 
        "longitude": 135.76597151598833,
        "name": "NOONE",
        "hours": {
            "Monday": "12:00 - 20:00",
            "Tuesday": "12:00 - 20:00",
            "Wednesday": "12:00 - 20:00",
            "Thursday": "12:00 - 20:00",
            "Friday": "12:00 - 20:00",
            "Saturday": "12:00 - 20:00",
            "Sunday": "12:00 - 20:00"
        },
        "closed": ["Wednesday"],
        "contact": "075-201-1004"
    },
    "PROOF": {
        "address": "〒604-8035 京都府京都市中京区桜之町４０７−１ カレッジタウン詩の小路ビル 4F",
        "latitude": 35.00827396370308, 
        "longitude": 135.76740917996395,
        "name": "PROOF",
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
        "contact": "075-255-0007"
    },
    "Graphpaper kyoto": {
        "address": "〒604-8073 京都府京都市中京区大黒町88−１",
        "latitude": 35.007658825255305, 
        "longitude": 135.76522049749363,
        "name": "Graphpaper kyoto",
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
        "contact": "075-212-2228"
    },
}

# データベースへの書き込み
for store_id, store_info in stores_data.items():
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")
