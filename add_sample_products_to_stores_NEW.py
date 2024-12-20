import firebase_admin
from firebase_admin import credentials, firestore
import random
import re

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# カテゴリ一覧（サンプル）
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

# 全30店舗分、1店舗あたり4カテゴリ、合計120カテゴリ必要
# 各カテゴリを12回ずつ登場させる（10カテゴリ x 12回 = 120）
categories_multiplied = categories * 12
random.shuffle(categories_multiplied)

# 参考用の画像URL(色別)
color_image_urls = {
    "Red": "https://via.placeholder.com/1024/ff0000?text=Red+Sample",
    "Blue": "https://via.placeholder.com/1024/0000ff?text=Blue+Sample",
    "Green": "https://via.placeholder.com/1024/00ff00?text=Green+Sample",
    "Black": "https://via.placeholder.com/1024/000000?text=Black+Sample",
    "White": "https://via.placeholder.com/1024/ffffff?text=White+Sample"
}

# 万一color_image_urlsになくても安全なフォールバック
fallback_image_url = "https://via.placeholder.com/1024?text=No+Image"

def generate_sample_stores(num_stores=30):
    # 営業時間サンプル
    hours_template = {
        "Monday": "10:00 - 19:00",
        "Tuesday": "10:00 - 19:00",
        "Wednesday": "10:00 - 19:00",
        "Thursday": "10:00 - 19:00",
        "Friday": "10:00 - 20:00",
        "Saturday": "11:00 - 20:00",
        "Sunday": "11:00 - 18:00"
    }

    stores_data = {}
    for i in range(1, num_stores + 1):
        store_id = f"store_{i:03d}"
        store_name = f"サンプル店舗{i}"

        # 京都付近のランダム座標
        latitude = round(random.uniform(35.000, 35.020), 8)
        longitude = round(random.uniform(135.750, 135.780), 8)

        # サンプル住所
        address = f"京都府京都市中京区サンプル町{i}番地"

        closed = []
        contact = f"075-123-45{i:02d}"

        store_info = {
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "name": store_name,
            "hours": hours_template,
            "closed": closed,
            "contact": contact
        }

        stores_data[store_id] = store_info

    return stores_data

# 30店舗分のサンプルデータ生成
stores_data = generate_sample_stores(30)

# 選ぶカテゴリ数と1カテゴリあたりの商品数
num_categories_per_store = 4
num_items_per_category = 10

colors = ["Red", "Blue", "Green", "Black", "White"]
sizes = ["S", "M", "L", "XL"]

for store_index, (store_id, store_info) in enumerate(stores_data.items()):
    # 店舗情報登録
    db.collection("stores").document(store_id).set(store_info)
    print(f"店舗 '{store_info['name']}' (ID: {store_id}) を登録しました。")

    # この店舗に割り当てる4カテゴリを取得
    start_idx = store_index * num_categories_per_store
    end_idx = start_idx + num_categories_per_store
    store_categories = categories_multiplied[start_idx:end_idx]

    # カテゴリ情報登録
    for cat in store_categories:
        category_ref = db.collection("stores").document(store_id).collection("categories").document(cat["id"])
        category_ref.set(cat)
        print(f"店舗 '{store_info['name']}' (ID: {store_id}) にカテゴリ '{cat['name']}' を登録しました。")

    # 商品情報登録
    for cat in store_categories:
        for i in range(1, num_items_per_category + 1):
            product_name = f"サンプル{cat['name']}{i}"
            price = random.choice([1000, 1500, 2000, 2500, 3000])
            color = random.choice(colors)
            item_sizes = sizes
            
            # カラーに対応する画像URLを取得
            image_url = color_image_urls.get(color, fallback_image_url)

            # ドキュメントID生成
            safe_cat_id = cat["id"].replace("/", "_")
            safe_color = color.replace("/", "_")
            doc_id = f"{safe_cat_id}_{i}_{safe_color}"

            item_ref = db.collection("stores").document(store_id).collection("items").document(doc_id)
            doc_data = {
                "product_name": product_name,
                "price": price,
                "category_id": cat["id"],
                "store_id": store_id,
                "color": color,
                "sizes": item_sizes,
                "image_url": image_url
            }
            item_ref.set(doc_data)

        print(f"店舗 '{store_info['name']}' (ID: {store_id}) のカテゴリ '{cat['name']}' に {num_items_per_category}個の商品を追加しました。")

print("すべての店舗にカテゴリとサンプル商品（色に合わせた画像URL付）を保存しました！")
