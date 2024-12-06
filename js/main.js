// Firestore のインスタンスを取得
const db = firebase.firestore();

// 地図の初期化
const map = L.map('map').setView([35.0116, 135.7681], 13); // 京都市を中心に表示

// OpenStreetMap のタイルを追加
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// マーカーのデフォルトアイコン
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

// 選択されたマーカーのアイコン（赤色アイコン）
const selectedIcon = L.icon({
  iconUrl: 'marker-icon-red.png', // プロジェクト直下に配置してある赤いアイコンファイル
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

// マーカーを管理するためのレイヤーグループ
const markersLayer = L.layerGroup().addTo(map);

// 現在選択されているマーカー
let currentSelectedMarker = null;

window.addEventListener('DOMContentLoaded', loadCategories);

async function loadCategories() {
  const categorySelect = document.getElementById('category-select');

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
  ];

  categories.forEach(category => {
    const categoryOption = document.createElement('option');
    categoryOption.value = category.id;
    categoryOption.textContent = category.name;
    categorySelect.appendChild(categoryOption);
  });

  if (categorySelect.options.length > 0) {
    categorySelect.selectedIndex = 0;
    searchItems(); 
  }
}

document.getElementById('category-select').addEventListener('change', searchItems);

const sidebar = document.getElementById('sidebar');
const detailPanel = document.getElementById("detail-panel");

// 検索関数
async function searchItems() {
  const categorySelect = document.getElementById('category-select');
  const selectedCategory = categorySelect.value;

  markersLayer.clearLayers();
  document.getElementById("store-list").innerHTML = "";
  document.getElementById("detail-content").innerHTML = "";
  detailPanel.style.display = "none";
  detailPanel.classList.remove('open', 'expanded');

  if (window.innerWidth <= 768) {
    sidebar.classList.remove('open');
  }

  let query;
  if (selectedCategory) {
    // 全店舗横断で items を検索
    query = db.collectionGroup('items').where('category_id', '==', selectedCategory);
  } else {
    alert("カテゴリを選択してください。");
    return;
  }

  const querySnapshot = await query.get();

  if (querySnapshot.empty) {
    alert("該当する商品が見つかりませんでした。");
    return;
  }

  // 商品が見つかったのでサイドバーを表示
  sidebar.style.display = "block";
  if (window.innerWidth <= 768) {
    sidebar.classList.add('open');
  }

  const storeItemsMap = {};

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

  for (const storeId in storeItemsMap) {
    const items = storeItemsMap[storeId];

    const storeRef = db.collection("stores").doc(storeId);
    const storeDoc = await storeRef.get();

    if (storeDoc.exists) {
      const store = storeDoc.data();

      const marker = L.marker([store.latitude, store.longitude], { icon: defaultIcon }).addTo(markersLayer);
      marker.storeId = storeId;

      marker.on('click', () => {
        showDetailPanel(store, items);
        if (currentSelectedMarker && currentSelectedMarker !== marker) {
          currentSelectedMarker.setIcon(defaultIcon);
        }
        marker.setIcon(selectedIcon);
        currentSelectedMarker = marker;
      });

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

        if (currentSelectedMarker && currentSelectedMarker !== marker) {
          currentSelectedMarker.setIcon(defaultIcon);
        }
        marker.setIcon(selectedIcon);
        currentSelectedMarker = marker;
      };
      storeList.appendChild(storeItem);
    }
  }
}

function showDetailPanel(store, items) {
  const detailContent = document.getElementById("detail-content");
  detailContent.innerHTML = '';

  detailContent.innerHTML += `
    <h3>${store.name}</h3>
    <p>住所: ${store.address}</p>
    <hr>
    <h4>商品一覧</h4>
  `;

  // 画像表示追加: image_urlがあれば商品画像を表示
  items.forEach(item => {
    const imageHtml = item.image_url ? `<img src="${item.image_url}" alt="${item.variant_name}" style="max-width:100px;height:auto;"><br>` : '';
    detailContent.innerHTML += `
      <div class="result-item">
        <strong>${item.variant_name}</strong><br>
        ${imageHtml}
        価格: ¥${item.price}<br><br>
      </div>
    `;
  });

  detailPanel.style.display = "block";
  detailPanel.classList.add('open');

  if (window.innerWidth <= 768) {
    detailPanel.classList.add('open');
    sidebar.classList.remove('open');
  }
}

document.getElementById('close-detail').addEventListener('click', () => {
  detailPanel.style.display = "none";
  detailPanel.classList.remove('open', 'expanded');

  if (window.innerWidth <= 768) {
    sidebar.classList.add('open');
  }

  if (currentSelectedMarker) {
    currentSelectedMarker.setIcon(defaultIcon);
    currentSelectedMarker = null;
  }
});

let startY;
let startHeight;
let isDragging = false;

detailPanel.addEventListener('touchstart', (e) => {
  if (e.target !== detailPanel && !e.target.closest('.close-button')) return;
  isDragging = true;
  startY = e.touches[0].clientY;
  startHeight = detailPanel.offsetHeight;
});

detailPanel.addEventListener('touchmove', (e) => {
  if (!isDragging) return;
  const deltaY = startY - e.touches[0].clientY;
  let newHeight = startHeight + deltaY;

  newHeight = Math.max(window.innerHeight * 0.3, Math.min(window.innerHeight, newHeight));

  detailPanel.style.height = newHeight + 'px';

  if (newHeight >= window.innerHeight * 0.9) {
    detailPanel.classList.add('expanded');
  } else {
    detailPanel.classList.remove('expanded');
  }
});

detailPanel.addEventListener('touchend', () => {
  isDragging = false;
});
