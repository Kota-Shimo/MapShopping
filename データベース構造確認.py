import firebase_admin
from firebase_admin import credentials, firestore

# Firebase初期化
if not firebase_admin._apps:
    cred = credentials.Certificate("C:/Users/kotas/OneDrive/デスクトップ/MapShopping/firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

def print_document_structure(doc_ref, indent=0):
    """指定されたドキュメントの構造を表示（詳細なデータは出力しない）"""
    print(" " * indent + f"Document ID: {doc_ref.id}")
    doc = doc_ref.get().to_dict()
    if doc:
        for key, value in doc.items():
            if isinstance(value, dict):  # ネストされた辞書の場合
                print(" " * (indent + 2) + f"{key}: (Nested Document)")
                # ネストされた辞書のキーだけを表示
                for sub_key in value.keys():
                    print(" " * (indent + 4) + f"{sub_key}: ...")
            else:
                print(" " * (indent + 2) + f"{key}: {value}")

    # サブコレクションの存在を確認（内容は出力しない）
    subcollections = doc_ref.collections()
    for subcollection in subcollections:
        print(" " * (indent + 2) + f"Subcollection: {subcollection.id}")
        # サブコレクション内のドキュメント数をカウントして表示
        sub_doc_count = sum(1 for _ in subcollection.stream())
        print(" " * (indent + 4) + f"Document count: {sub_doc_count}")

def print_firestore_structure():
    """Firestore全体の構造を表示"""
    print("Firestore構造:")
    collections = db.collections()
    for collection in collections:
        print(f"Collection: {collection.id}")
        for doc in collection.stream():
            print_document_structure(doc.reference, 2)

# 実行
print_firestore_structure()
