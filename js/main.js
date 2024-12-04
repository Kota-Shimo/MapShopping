// Firestore のインスタンスを取得
const db = firebase.firestore();

// 地図の初期化
const map = L.map('map').setView([35.0116, 135.7681], 13); // 京都市を中心に表示

// OpenStreetMap のタイルを追加
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// マーカーを管理するためのレイヤーグループ
const markersLayer = L.layerGroup().addTo(map);

// ページロード時にカテゴリを取得してセレクトボックスに追加
window.addEventListener('DOMContentLoaded', loadCategories);

async function loadCategories() {
  const categorySelect = document.getElementById('category-select');
  
  // 洋服関連のカテゴリを設定
  const categories = [
    { id: 'outerwear', name: 'アウターウェア' },
    { id: 'tops', name: 'トップス' },
    { id: 'bottoms', name: 'ボトムス' },
    { id: 'jackets', name: 'ジャケット' },
    { id: 'shirts', name: 'シャツ' },
    { id: 'pants', name: 'パンツ' },
    { id: 'sweatshirts', name: 'スウェットシャツ' },
    { id: 't-shirts', name: 'Tシャツ' },
    { id: 'denim', name: 'デニム' },
    { id: 'accessories', name: 'アクセサリー' },
    // 他のカテゴリを追加
  ];

  categories.forEach(category => {
    const categoryOption = document.createElement('option');
    categoryOption.value = category.id;
    categoryOption.textContent = category.name;
    categorySelect.appendChild(categoryOption);
  });

  // カテゴリがロードされたら最初のカテゴリを選択
  if (categorySelect.options.length > 0) {
    categorySelect.selectedIndex = 0;
    searchItems(); // 最初のカテゴリで検索を実行
  }
}

// カテゴリが変更されたときに検索を実行
document.getElementById('category-select').addEventListener('change', searchItems);

// 検索関数
async function searchItems() {
  const categorySelect = document.getElementById('category-select');
  const selectedCategory = categorySelect.value;

  // 地図と検索結果をクリア
  markersLayer.clearLayers();
  document.getElementById("store-list").innerHTML = "";
  document.getElementById("detail-content").innerHTML = "";
  document.getElementById("detail-panel").style.display = "none";

  let query;

  if (selectedCategory) {
    // 特定のカテゴリ内で検索
    query = db.collection('categories').doc(selectedCategory).collection('items');
  } else {
    // カテゴリが選択されていない場合は何もしない
    alert("カテゴリを選択してください。");
    return;
  }

  const querySnapshot = await query.get();

  if (querySnapshot.empty) {
    alert("該当する商品が見つかりませんでした。");
    return;
  }

  // 店舗ごとに商品をグループ化
  const storeItemsMap = {}; // store_id をキー、商品リストを値とするオブジェクト

  querySnapshot.forEach(doc => {
    const item = doc.data();
    const storeId = item.store_id;
    if (!storeItemsMap[storeId]) {
      storeItemsMap[storeId] = [];
    }
    storeItemsMap[storeId].push(item);
  });

  if (Object.keys(storeItemsMap).length === 0) {
    alert("該当する商品が見つかりませんでした。");
    return;
  }

  // 店舗ごとに処理
  for (const storeId in storeItemsMap) {
    const items = storeItemsMap[storeId];

    // 店舗情報を取得
    const storeRef = db.collection("stores").doc(storeId);
    const storeDoc = await storeRef.get();

    if (storeDoc.exists) {
      const store = storeDoc.data();

      // マーカーを追加
      const marker = L.marker([store.latitude, store.longitude]).addTo(markersLayer);
      marker.storeId = storeId; // マーカーに storeId を付加

      // マーカーのクリックイベント
      marker.on('click', () => {
        showDetailPanel(store, items);
      });

      // 店舗リストに追加
      const storeList = document.getElementById("store-list");
      const storeItem = document.createElement("div");
      storeItem.className = "store-item";
      storeItem.innerHTML = `
        <strong>${store.name}</strong><br>
        住所: ${store.address}
      `;
      storeItem.onclick = () => {
        map.setView([store.latitude, store.longitude], 16);
        marker.openPopup();
        showDetailPanel(store, items);
      };
      storeList.appendChild(storeItem);
    }
  }
}

// 詳細パネルを表示する関数
function showDetailPanel(store, items) {
  const detailPanel = document.getElementById("detail-panel");
  const detailContent = document.getElementById("detail-content");

  // パネルの内容をクリア
  detailContent.innerHTML = '';

  // 店舗情報を表示
  detailContent.innerHTML += `
    <h3>${store.name}</h3>
    <p>住所: ${store.address}</p>
    <hr>
    <h4>商品一覧</h4>
  `;

  // 商品リストを表示
  items.forEach(item => {
    detailContent.innerHTML += `
      <div class="result-item">
        <strong>${item.variant_name}</strong><br>
        価格: ¥${item.price}<br><br>
      </div>
    `;
  });

  // 詳細パネルを表示
  detailPanel.style.display = "block";
}

// 詳細パネルを閉じるボタンのイベントリスナー
document.getElementById('close-detail').addEventListener('click', () => {
  document.getElementById("detail-panel").style.display = "none";
});
