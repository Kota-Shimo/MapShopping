// Firestore のインスタンスを取得
const db = firebase.firestore();

// 地図の初期化
const map = L.map('map').setView([35.0116, 135.7681], 13); 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

const selectedIcon = L.icon({
  iconUrl: 'marker-icon-red.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

const markersLayer = L.layerGroup().addTo(map);
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

async function searchItems() {
  const categorySelect = document.getElementById('category-select');
  const selectedCategory = categorySelect.value;

  markersLayer.clearLayers();
  document.getElementById("store-list").innerHTML = "";
  document.getElementById("detail-content").innerHTML = "";

  // detail-panelをcollapsedに
  detailPanel.classList.remove('open','expanded','collapsed');
  detailPanel.classList.add('collapsed');
  // collapsedでheight:0%となるためdisplay:blockのままでOK

  if (window.innerWidth <= 768) {
    sidebar.classList.remove('open');
  }

  let query;
  if (selectedCategory) {
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

  // 表示をopen状態に
  detailPanel.classList.remove('collapsed','expanded');
  detailPanel.classList.add('open');

  if (window.innerWidth <= 768) {
    detailPanel.classList.add('open');
    sidebar.classList.remove('open');
  }
}

document.getElementById('close-detail').addEventListener('click', () => {
  detailPanel.classList.remove('open','expanded');
  detailPanel.classList.add('collapsed');

  if (window.innerWidth <= 768) {
    sidebar.classList.add('open');
  }

  if (currentSelectedMarker) {
    currentSelectedMarker.setIcon(defaultIcon);
    currentSelectedMarker = null;
  }
});

// スライディングシートのドラッグ処理
let startY;
let startHeight;
let isDragging = false;
const handleBar = document.querySelector('#detail-panel .handle-bar');

handleBar.addEventListener('touchstart', (e) => {
  isDragging = true;
  startY = e.touches[0].clientY;
  startHeight = detailPanel.offsetHeight;
});

handleBar.addEventListener('touchmove', (e) => {
  if (!isDragging) return;
  const deltaY = startY - e.touches[0].clientY;
  let newHeight = startHeight + deltaY;

  const screenHeight = window.innerHeight;
  newHeight = Math.max(0, Math.min(screenHeight, newHeight));

  detailPanel.style.height = newHeight + 'px';
});

handleBar.addEventListener('touchend', () => {
  isDragging = false;
  const currentHeight = detailPanel.offsetHeight;
  const screenHeight = window.innerHeight;
  const ratio = currentHeight / screenHeight;

  if (ratio >= 0.7) {
    detailPanel.classList.remove('open','collapsed');
    detailPanel.classList.add('expanded');
    detailPanel.style.height = '100%';
  } else if (ratio >= 0.3) {
    detailPanel.classList.remove('expanded','collapsed');
    detailPanel.classList.add('open');
    detailPanel.style.height = '50%';
  } else {
    detailPanel.classList.remove('open','expanded');
    detailPanel.classList.add('collapsed');
    detailPanel.style.height = '0%';
  }
});
