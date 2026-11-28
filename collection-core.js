// collection-core.js — コレクション図鑑(collection.html)と全カード図鑑(category.html)の共通処理
// ページ差分は window.COLLECTION_CORE_CONFIG で渡す（未指定は collection.html の挙動）。
const CORE_CFG = Object.assign({
    alwaysColoredCards: false,  // true: 未取得でも常に色付き表示（category）
    editionStatsHeading: false, // true: 弾数別進捗の見出しをJS側で付ける（category）
    initStatsOnLoad: true,       // 初期ロード時に都道府県別・弾数別統計を描画する
    initLocationOnLoad: true     // 初期ロード時に現在地の都道府県を初期値にする
}, window.COLLECTION_CORE_CONFIG || {});

const prefOrder = ["世界", "その他", "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県",
    "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県",
    "宮崎県", "鹿児島県", "沖縄県"];
let masterData = [];
let userStats = JSON.parse(localStorage.getItem('manhole_collection')) || {};
let isSelectionMode = false;
let selectedIds = new Set();
let currentId = null;
let currentCity = null;

// --- ローカルストレージのキーを「名前」から「ID」へ完全マイグレーション ---
async function migrateAddIdsToLocalStorage() {
    const storageKey = 'manhole_collection';
    const rawData = localStorage.getItem(storageKey);
    if (!rawData) return;

    // 読み込み済みの masterData があれば再利用する（なければ取得）
    const masterDataList = masterData.length ? masterData : await (await fetch('master_data.json')).json();

    const normalize = (str) => {
        if (!str) return '';
        return str
            .replace(/\s+/g, '')
            .replace(/（/g, '(').replace(/）/g, ')');
    };

    const masterMap = {};
    masterDataList.forEach(item => {
        if (item.old_id) {
            masterMap[normalize(item.old_id)] = item.id;
        }
    });

    const localData = JSON.parse(rawData);
    const newLocalData = {};
    let updatedCount = 0;
    let skippedKeys = [];

    Object.keys(localData).forEach(oldIdKey => {
        const normKey = normalize(oldIdKey);

        let matchedId = masterMap[normKey];

        if (!matchedId) {
            const baseName = normalize(oldIdKey.replace(/\s*\([^\)]+\)/, ''));
            matchedId = masterMap[baseName];
        }

        const isAlreadyId = masterDataList.some(m => m.id === oldIdKey);

        if (isAlreadyId) {
            newLocalData[oldIdKey] = localData[oldIdKey];
        } else if (matchedId) {
            const itemData = localData[oldIdKey];
            itemData.id = matchedId;
            newLocalData[matchedId] = itemData; // キーをIDに統一！
            updatedCount++;
        } else {
            newLocalData[oldIdKey] = localData[oldIdKey];
            skippedKeys.push(oldIdKey);
        }
    });

    localStorage.setItem(storageKey, JSON.stringify(newLocalData));
    userStats = newLocalData;

    console.log(`✅ ${updatedCount} 件のデータをIDキーへ移行・更新しました！`);
    if (skippedKeys.length > 0) {
        console.warn("⚠️ master_data に見つからずID移行できなかったキー:", skippedKeys);
    }
}

// 位置情報から都道府県を特定する関数
async function setInitialLocation() {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(async (position) => {
        try {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`);
            const data = await res.json();

            if (data && data.address && data.address.province) {
                let detectedPref = data.address.province;
                const pSel = document.getElementById('prefFilter');
                if (pSel) {
                    for (let i = 0; i < pSel.options.length; i++) {
                        if (detectedPref.includes(pSel.options[i].value) && pSel.options[i].value !== "") {
                            pSel.value = pSel.options[i].value;
                            handleFilterChange();
                            break;
                        }
                    }
                }
            }
        } catch (error) { console.error("Location detection error:", error); }
    }, (error) => {
        console.log("位置情報の取得が拒否されました");
    });
}

// 初期ロード
fetch('master_data.json').then(res => res.json()).then(async (data) => {
    masterData = data;
    await migrateAddIdsToLocalStorage();
    updateStats();
    initFilters();
    if (CORE_CFG.initStatsOnLoad) {
        updatePrefStats();
        updateEditionStats();
    }

    if (CORE_CFG.initLocationOnLoad && document.getElementById('prefFilter').value === "") {
        setInitialLocation();
    }
}).catch(err => console.error("マスターデータの読み込みエラー:", err));


// 全体統計の更新
function updateStats() {
    const total = masterData.length;
    const collectedCards = masterData.filter(card => {
        const stat = getCardStat(card);
        return stat && stat.collected;
    });

    const collectedCount = collectedCards.length;

    const datedCount = collectedCards.filter(card => {
        const stat = getCardStat(card);
        return stat && stat.date && stat.date !== "";
    }).length;

    // 日付登録率は購入分（日付を持たない仕様）を分母から除外する
    const visitCollectedCount = collectedCards.filter(card => {
        const stat = getCardStat(card);
        return stat && stat.method !== 'purchase';
    }).length;

    const collectRate = total > 0 ? Math.round((collectedCount / total) * 100) : 0;
    const dateRate = visitCollectedCount > 0 ? Math.round((datedCount / visitCollectedCount) * 100) : 0;

    const statsText = document.querySelector('.stats-text');
    if (statsText) {
        statsText.innerHTML = `
    <div style="display:flex; flex-direction:column; align-items:center; gap:2px;">
        <div>
            <span style="color: #4dabff; font-size: 1.1em;">${collectedCount}</span> / <span>${total}</span>
            <small>収集</small>
            <span class="rate-badge" style="margin-left:8px;">収集率: ${collectRate}%</span>
        </div>
        <div style="font-size: 11px; color: #ffc107; margin-top: 2px;">
            日付登録済み: ${datedCount}枚 (登録率: ${dateRate}%)
        </div>
    </div>
    `;
    }
    const totalProg = document.getElementById('totalProgress');
    const dateProg = document.getElementById('dateProgress');
    if (totalProg) totalProg.style.width = collectRate + '%';
    if (dateProg) dateProg.style.width = dateRate + '%';
}

function initFilters() {
    const pSel = document.getElementById('prefFilter');
    const eSel = document.getElementById('editionFilter');
    if (!pSel || !eSel) return;
    pSel.innerHTML = '<option value="">都道府県を選択</option>';
    eSel.innerHTML = '<option value="">弾数を選択</option>';

    prefOrder.forEach(p => {
        if (masterData.some(d => d.pref === p)) {
            pSel.innerHTML += `<option value="${p}">${p}</option>`;
        }
    });

    const eds = [...new Set(masterData.map(d => d.edition))].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    eds.forEach(e => eSel.innerHTML += `<option value="${e}">${e}</option>`);
}

function toggleSelectionMode() {
    isSelectionMode = !isSelectionMode;
    if (!isSelectionMode) {
        selectedIds.clear();
    }
    renderCollection();
}

function selectAllFiltered() {
    const pref = document.getElementById('prefFilter').value;
    const ed = document.getElementById('editionFilter').value;
    let filtered = masterData.filter(d => (!pref || d.pref === pref) && (!ed || d.edition === ed));

    const allSelected = filtered.every(c => selectedIds.has(c.id));
    filtered.forEach(c => {
        const el = document.querySelector(`[data-id="${c.id}"]`);
        if (allSelected) {
            selectedIds.delete(c.id);
            if (el) el.classList.remove('selecting-active');
        } else {
            selectedIds.add(c.id);
            if (el) el.classList.add('selecting-active');
        }
    });
    updateBulkButtonUI();
}

function handleSearchInput() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    const searchVal = searchInput.value;

    const filterGroup = document.getElementById('filterGroup');
    if (searchVal.length > 0) {
        if (clearBtn) clearBtn.style.display = 'flex';
        document.getElementById('prefFilter').value = "";
        document.getElementById('editionFilter').value = "";
        if (filterGroup) {
            filterGroup.style.opacity = "0.3";
            filterGroup.style.pointerEvents = "none";
        }
    } else {
        if (clearBtn) clearBtn.style.display = 'none';
        if (filterGroup) {
            filterGroup.style.opacity = "1";
            filterGroup.style.pointerEvents = "auto";
        }
    }
    renderCollection();
}

function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = "";
        handleSearchInput();
        searchInput.focus();
    }
}

// ★追加: 選択中のコラボフィルターを保持する変数
let currentCollab = "";

// ★追加: コラボボタンを押した時の処理

function toggleCollabSection() {
    const area = document.getElementById('collabButtons');
    const btn = document.getElementById('collabToggleBtn');
    if (!area) return;
    const isOpen = area.style.display !== 'none';
    area.style.display = isOpen ? 'none' : 'flex';
    if (btn) btn.textContent = isOpen ? '開く ▼' : '閉じる ▲';
}

function setCollabFilter(val, btn) {
    currentCollab = val;
    const cc = document.getElementById('collabCurrent');
    if (cc) cc.textContent = val ? `選択中: ${val}` : '';

    // ボタンのハイライト切り替え
    document.querySelectorAll('.collab-btn').forEach(b => {
        b.classList.remove('active');
        b.style.background = '#222';
        b.style.color = '#aaa';
        b.style.borderColor = '#444';
    });
    if (btn) {
        btn.classList.add('active');
        btn.style.background = '#333';
        btn.style.color = '#fff';
        btn.style.borderColor = '#555';
    }

    // ★追加: コラボ（ガンダム・アイマスなど）を選択した時、都道府県・弾数・検索ワードをクリア
    if (currentCollab !== "") {
        document.getElementById('prefFilter').value = "";
        document.getElementById('editionFilter').value = "";
        document.getElementById('searchInput').value = "";
    }


    renderCollection();
}

function handleFilterChange() {
    const pref = document.getElementById('prefFilter').value;
    const ed = document.getElementById('editionFilter').value;

    if (pref !== "" || ed !== "") {
        document.getElementById('searchInput').value = "";
        const filterGroup = document.getElementById('filterGroup');
        if (filterGroup) {
            filterGroup.style.opacity = "1";
            filterGroup.style.pointerEvents = "auto";
        }
    }
    renderCollection();
}

// コレクションの描画
function renderCollection() {
    const pref = document.getElementById('prefFilter')?.value || "";
    const ed = document.getElementById('editionFilter')?.value || "";
    const searchText = (document.getElementById('searchInput')?.value || "").trim().toLowerCase();
    const uncollectedElem = document.getElementById('uncollectedFilter');
    const showUncollectedOnly = uncollectedElem ? uncollectedElem.checked : false;
    const listDiv = document.getElementById('collectionList');
    if (!listDiv) return;
    const bulkArea = document.getElementById('bulkActionArea');
    const statsDiv = document.getElementById('filterStats');

    let filtered = [];

    if (searchText !== "") {
        // 名前 (city) に加えて ID (id, old_id) で検索ヒット
        filtered = masterData.filter(d =>
            (d.city && d.city.toLowerCase().includes(searchText)) ||
            (d.id && d.id.toLowerCase().includes(searchText)) ||
            (d.old_id && d.old_id.toLowerCase().includes(searchText))
        );
    } else if (pref || ed || showUncollectedOnly || currentCollab !== "") {
        filtered = masterData.filter(d => {
            const pMatch = !pref || d.pref === pref;
            const eMatch = !ed || d.edition === ed;

            const cMatch = !currentCollab || (d.tags && Array.isArray(d.tags) && d.tags.includes(currentCollab));

            return pMatch && eMatch && cMatch;
        });
    } else {
        listDiv.innerHTML = '<div class="empty-state">検索ワード（市町村名・カードID）を入力するか、<br>条件から絞り込んでください</div>';
        if (bulkArea) bulkArea.style.display = 'none';
        if (statsDiv) statsDiv.style.display = 'none';
        return;
    }

    // 「未取得のみ表示」がONの場合、取得済みのものを除外
    if (showUncollectedOnly) {
        filtered = filtered.filter(c => {
            const stats = getCardStat(c);
            return !stats || !stats.collected;
        });
    }

    // フィルター内統計（IDベースで判定）
    if (statsDiv) {
        const totalInFilter = filtered.length;
        const collectedInFilter = filtered.filter(c => getCardStat(c)?.collected);
        const collectedCount = collectedInFilter.length;
        const datedCountInFilter = collectedInFilter.filter(c => getCardStat(c)?.date).length;
        const visitCountInFilter = collectedInFilter.filter(c => getCardStat(c)?.method !== 'purchase').length;
        const dateRateInFilter = visitCountInFilter > 0 ? Math.round((datedCountInFilter / visitCountInFilter) * 100) : 0;
        const collectRateInFilter = totalInFilter > 0 ? Math.round((collectedCount / totalInFilter) * 100) : 0;

        statsDiv.style.display = 'block';
        statsDiv.innerHTML = `
<div style="margin-bottom: 5px;">
表示中: <b>${totalInFilter}</b>枚 / 取得済み: <b>${collectedCount}</b>枚
<span class="rate-badge" style="margin-left:5px;">収集率: ${collectRateInFilter}%</span>
</div>
<div style="font-size: 11px; color: #ffc107;">
表示内の日付登録: <b>${datedCountInFilter}</b>枚 (登録率: ${dateRateInFilter}%)
</div>
`;
    }

    if (bulkArea) bulkArea.style.display = (filtered.length > 0) ? 'block' : 'none';
    updateBulkButtonUI();

    // カード描画処理
    listDiv.innerHTML = filtered.map(c => {
        if (!c.url) return '';
        const stats = getCardStat(c);
        const isCollected = stats?.collected;
        const isSelected = selectedIds.has(c.id);
        const hasDate = stats?.date && stats.date !== "";
        const collectDateText = hasDate ? stats.date.replace(/-/g, '.') : (isCollected && stats?.method !== 'purchase' ? "日付未登録" : "");

        const memoText = stats?.memo ?
            `<div style="font-size:9px; color:#aaa; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; margin-top:2px;">
        ${stats.memo}</div>`
            : "";

        const methodBadge = (isCollected && stats?.method === 'purchase') ?
            `<div style="font-size:9px; color:#ffc107; margin-top:2px;">🛒購入${(stats.price !== undefined && stats.price !== null && stats.price !== "" && !isNaN(Number(stats.price))) ? ` ${Number(stats.price).toLocaleString()}円` : ""}</div>`
            : "";

        let statusClass = CORE_CFG.alwaysColoredCards ? 'collected' : (isCollected ? 'collected' : '');
        if (isSelectionMode && isSelected) statusClass = 'selecting-active';

        return `
<div class="card-container ${statusClass}" data-id="${c.id}" onclick="handleCardClick('${c.id}')">
${CORE_CFG.alwaysColoredCards ? '' : '<div class="check-mark">✓</div>'}
<img src="${c.url}" loading="lazy" alt="${c.city}" onerror="this.style.opacity='0.3';this.onerror=null;">
<div class="card-info">
    <div style="font-weight:bold;">${c.city}</div>
    ${memoText}${methodBadge}
    <div class="date-text" style="font-size: 10px; color: ${hasDate ? '#4dabff' : '#ffc107'}; height: 12px; margin-top: 2px;">
        ${collectDateText}
    </div>
</div>
</div>
`;
    }).join('');
}

function handleCardClick(cardId) {
    const cityData = masterData.find(d => d.id === cardId);
    if (!cityData) return;

    if (isSelectionMode) {
        const cardElement = document.querySelector(`[data-id="${cardId}"]`);
        if (selectedIds.has(cardId)) {
            selectedIds.delete(cardId);
            if (cardElement) cardElement.classList.remove('selecting-active');
        } else {
            selectedIds.add(cardId);
            if (cardElement) cardElement.classList.add('selecting-active');
        }
        updateBulkButtonUI();
    } else {
        openModal(cardId);
    }
}

function updateBulkButtonUI() {
    const bulkBtn = document.getElementById('bulkCollectBtn');
    const bulkDateArea = document.getElementById('bulkDateArea');
    const selectAllBtn = document.getElementById('selectAllBtn');

    if (isSelectionMode) {
        bulkBtn.onclick = executeBulkRegistration;
        bulkBtn.textContent = selectedIds.size > 0 ? `${selectedIds.size}枚を一括登録・更新` : "キャンセル";
        if (selectAllBtn) selectAllBtn.style.display = 'block';
        if (bulkDateArea) bulkDateArea.style.display = (selectedIds.size > 0) ? 'flex' : 'none';
        if (selectedIds.size === 0) bulkBtn.onclick = toggleSelectionMode;
    } else {
        bulkBtn.onclick = toggleSelectionMode;
        bulkBtn.textContent = "カードを選択して登録";
        if (selectAllBtn) selectAllBtn.style.display = 'none';
        if (bulkDateArea) bulkDateArea.style.display = 'none';
    }
}

function executeBulkRegistration() {
    if (selectedIds.size === 0) return;
    let targetDate = document.getElementById('bulkDateInput').value;
    const dateMsg = targetDate ? `${targetDate} で` : "日付なしで";
    if (!confirm(`${selectedIds.size}枚を ${dateMsg}一括登録しますか？`)) return;

    selectedIds.forEach(id => {
        const d = masterData.find(x => x.id === id);
        const cityName = d ? d.city : "";

        const existingStat = getCardStat(d);
        const existingMemo = existingStat?.memo || "";
        const existingMethod = existingStat?.method === 'purchase' ? 'purchase' : 'visit';
        const existingPrice = existingMethod === 'purchase' ? (existingStat?.price ?? "") : "";

        // IDをキーとして保存
        userStats[id] = {
            collected: true,
            date: existingMethod === 'purchase' ? "" : targetDate,
            memo: existingMemo,
            method: existingMethod,
            price: existingPrice,
            city: cityName,
            id: id
        };

        // 古い名前キーがあれば削除
        const oldFullKey = `${cityName} (${id})`;
        if (userStats[oldFullKey]) delete userStats[oldFullKey];
        if (userStats[cityName]) delete userStats[cityName];
    });

    isSelectionMode = false;
    selectedIds.clear();
    saveAndRefresh();
}

function openModal(cardId) {
    const d = masterData.find(x => x.id === cardId);
    if (!d) return;

    currentId = d.id;
    currentCity = d.city;

    const saved = getCardStat(d) || { collected: false, date: "", memo: "" };

    document.getElementById('modalImg').src = d.url;
    document.getElementById('modalTitle').textContent = d.city;
    document.getElementById('modalSub').textContent = `${d.pref} / ${d.edition}`;
    document.getElementById('memoInput').value = saved.memo || "";
    const methodSel = document.getElementById('collectMethod');
    if (methodSel) methodSel.value = saved.method === 'purchase' ? 'purchase' : 'visit';
    const priceInput = document.getElementById('purchasePrice');
    if (priceInput) priceInput.value = (saved.method === 'purchase' && saved.price !== undefined && saved.price !== null) ? saved.price : "";
    togglePriceField();

    const dateInput = document.getElementById('collectDate');
    const dateDisplay = document.getElementById('modalDate');

    if (saved.collected && saved.date) {
        dateInput.value = saved.date;
        const yearMonth = saved.date.substring(0, 7);

        dateDisplay.innerHTML = `
    <div style="display: flex; justify-content: flex-end; margin-top: 4px;">
        <a href="calender.html?target=${yearMonth}" style="
            background: rgba(77, 171, 255, 0.15);
            color: #4dabff;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            text-decoration: none;
            border: 1px solid rgba(77, 171, 255, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-weight: bold;
            transition: all 0.2s;
           "
            onmouseover="this.style.background='rgba(77, 171, 255, 0.25)'; this.style.transform='translateY(-1px)';"
            onmouseout="this.style.background='rgba(77, 171, 255, 0.15)'; this.style.transform='translateY(0)';">
            <span>この月の履歴を確認</span>
            <span style="font-size: 14px; line-height: 1;">›</span>
        </a>
    </div>`;
    } else {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
        dateDisplay.innerHTML = `
    <div style="text-align: right; margin-top: 4px;">
        <span style="font-size: 10px; color: #666; border: 1px solid #444; padding: 2px 8px; border-radius: 10px;">
            未登録
        </span>
    </div>`;
    }

    const getBtn = document.getElementById('getBtn');
    const delBtn = document.getElementById('deleteBtn');

    if (saved.collected) {
        getBtn.textContent = '更新して保存';
        getBtn.style.background = '#28a745';
        delBtn.style.display = 'block';
    } else {
        getBtn.textContent = '取得済みにする';
        getBtn.style.background = '#4dabff';
        delBtn.style.display = 'none';
    }

    document.getElementById('modal').style.display = 'flex';
}

function togglePriceField() {
    const methodSel = document.getElementById('collectMethod');
    const priceRow = document.getElementById('priceRow');
    if (!methodSel || !priceRow) return;
    const isPurchase = methodSel.value === 'purchase';
    priceRow.style.display = isPurchase ? 'flex' : 'none';
    // 購入の場合は日付を記録しない（収集推移・カレンダーに出さないため）
    const dateRow = document.getElementById('dateRow');
    if (dateRow) dateRow.style.display = isPurchase ? 'none' : 'flex';
    const modalDate = document.getElementById('modalDate');
    if (modalDate) modalDate.style.display = isPurchase ? 'none' : 'block';
}

function toggleCollect() {
    const memoVal = document.getElementById('memoInput').value;
    const methodVal = document.getElementById('collectMethod')?.value === 'purchase' ? 'purchase' : 'visit';
    const dateVal = methodVal === 'purchase' ? "" : document.getElementById('collectDate').value;
    const priceRaw = document.getElementById('purchasePrice')?.value;
    const priceVal = (methodVal === 'purchase' && priceRaw !== "" && priceRaw !== null && priceRaw !== undefined) ? Number(priceRaw) : "";

    const d = masterData.find(x => x.id === currentId);
    const saved = d ? getCardStat(d) : null;
    const isAlreadyCollected = saved && saved.collected;

    // IDを主キーとして保存
    userStats[currentId] = {
        collected: true,
        date: dateVal,
        memo: memoVal,
        method: methodVal,
        price: priceVal,
        city: currentCity,
        id: currentId
    };

    // 古いキーを削除
    const oldFullKey = `${currentCity} (${currentId})`;
    if (userStats[oldFullKey]) delete userStats[oldFullKey];
    if (userStats[currentCity]) delete userStats[currentCity];

    if (!isAlreadyCollected) {
        celebrate();
    }

    saveAndRefresh();
}

function deleteCollect() {
    if (confirm(`${currentCity} を削除しますか？`)) {
        delete userStats[currentId];

        const oldFullKey = `${currentCity} (${currentId})`;
        if (userStats[oldFullKey]) delete userStats[oldFullKey];
        if (userStats[currentCity]) delete userStats[currentCity];

        saveAndRefresh();
    }
}

function saveAndRefresh() {
    localStorage.setItem('manhole_collection', JSON.stringify(userStats));
    scheduleAutoBackup();
    updateStats();
    renderCollection();
    setTimeout(() => closeModal(), 600);
    updatePrefStats();
    updateEditionStats();
}

function closeModal() { document.getElementById('modal').style.display = 'none'; }

function goToSearchPage() {
    if (!currentCity) return;
    const d = masterData.find(x => x.city === currentCity);
    if (!d || !d.url) return;
    window.open(`search.html?img=${encodeURIComponent(d.url)}&city=${encodeURIComponent(d.city)}`, '_blank');
}

// --- Google Drive 自動バックアップ ---
const DRIVE_FILE_NAME = 'manhole_backup_auto.json';
let driveToken = null, driveTokenExpiry = 0, driveTokenClient = null, driveBackupTimer = null;

function driveClientId() { return localStorage.getItem('manhole_drive_client_id') || ''; }

function driveHash(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) { h = (Math.imul(31, h) + str.charCodeAt(i)) | 0; }
    return String(h);
}

function driveTokenValid() { return !!driveToken && Date.now() < driveTokenExpiry; }

function updateDriveStatus() {
    const el = document.getElementById('driveStatus');
    if (!el) return;
    const setup = document.getElementById('driveSetup');
    if (!driveClientId()) {
        el.textContent = '未設定：GoogleクライアントIDを入力してください';
        if (setup) setup.style.display = '';
        return;
    }
    if (setup) setup.style.display = 'none';
    const last = localStorage.getItem('manhole_drive_last_backup');
    const lastStr = last ? new Date(last).toLocaleString('ja-JP') : 'まだ';
    const data = localStorage.getItem('manhole_collection') || '{}';
    const dirty = localStorage.getItem('manhole_drive_backup_hash') !== driveHash(data);
    if (!driveTokenValid()) el.textContent = `ログインしていません（最終バックアップ: ${lastStr}）。自動保存にはログインが必要です`;
    else if (dirty) el.textContent = `ログイン中・バックアップ待ち…（最終: ${lastStr}）`;
    else el.textContent = `✅ 自動バックアップ有効（最終: ${lastStr}）`;
}

function saveDriveClientId() {
    const inp = document.getElementById('driveClientId');
    const v = (inp.value || '').trim();
    if (!v) { alert('クライアントIDを入力してください'); return; }
    localStorage.setItem('manhole_drive_client_id', v);
    updateDriveStatus();
    alert('保存しました。「Googleでログイン」を押してください');
}

function initDriveClient() {
    if (!driveClientId() || !(window.google && google.accounts && google.accounts.oauth2)) return false;
    if (driveTokenClient) return true;
    driveTokenClient = google.accounts.oauth2.initTokenClient({
        client_id: driveClientId(),
        scope: 'https://www.googleapis.com/auth/drive.file',
        callback: (resp) => {
            if (resp && resp.access_token) {
                driveToken = resp.access_token;
                driveTokenExpiry = Date.now() + (Number(resp.expires_in || 3600) - 60) * 1000;
                updateDriveStatus();
                scheduleAutoBackup(500);
            } else {
                alert('ログインできませんでした');
            }
        }
    });
    return true;
}

function driveLogin() {
    if (!driveClientId()) { alert('先にクライアントIDを入力して保存してください'); return; }
    if (!initDriveClient()) { alert('Googleログインの準備中です。数秒待ってからもう一度押してください'); return; }
    driveTokenClient.requestAccessToken();
}

function scheduleAutoBackup(delay = 4000) {
    updateDriveStatus();
    if (!driveClientId()) return;
    clearTimeout(driveBackupTimer);
    driveBackupTimer = setTimeout(runAutoBackup, delay);
}

async function driveApi(path, options = {}) {
    const r = await fetch('https://www.googleapis.com/' + path, {
        ...options,
        headers: { Authorization: 'Bearer ' + driveToken, ...(options.headers || {}) }
    });
    if (!r.ok) throw new Error('Drive API ' + r.status);
    return r;
}

async function driveFindFile() {
    const q = encodeURIComponent(`name='${DRIVE_FILE_NAME}' and trashed=false`);
    const data = await (await driveApi(`drive/v3/files?q=${q}&fields=files(id)`)).json();
    return (data.files && data.files.length) ? data.files[0].id : null;
}

async function runAutoBackup() {
    if (!driveTokenValid()) { updateDriveStatus(); return; }
    const data = localStorage.getItem('manhole_collection') || '{}';
    const h = driveHash(data);
    if (localStorage.getItem('manhole_drive_backup_hash') === h) { updateDriveStatus(); return; }
    try {
        const fileId = await driveFindFile();
        const boundary = 'mh' + Date.now();
        const metadata = { name: DRIVE_FILE_NAME, mimeType: 'application/json' };
        const body = `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(metadata)}\r\n--${boundary}\r\nContent-Type: application/json\r\n\r\n${data}\r\n--${boundary}--`;
        const headers = { 'Content-Type': 'multipart/related; boundary=' + boundary };
        if (fileId) {
            await driveApi(`upload/drive/v3/files/${fileId}?uploadType=multipart`, { method: 'PATCH', headers, body });
        } else {
            await driveApi('upload/drive/v3/files?uploadType=multipart', { method: 'POST', headers, body });
        }
        localStorage.setItem('manhole_drive_backup_hash', h);
        localStorage.setItem('manhole_drive_last_backup', new Date().toISOString());
    } catch (e) { console.warn('auto backup failed', e); }
    updateDriveStatus();
}

function driveBackupNow() {
    if (!driveTokenValid()) { alert('先にGoogleでログインしてください'); return; }
    runAutoBackup();
}

async function driveRestore() {
    if (!driveTokenValid()) { alert('先にGoogleでログインしてください'); return; }
    if (!confirm('Driveの自動バックアップで現在のデータを上書きしますか？')) return;
    try {
        const fileId = await driveFindFile();
        if (!fileId) { alert('Driveに自動バックアップが見つかりません'); return; }
        const text = await (await driveApi(`drive/v3/files/${fileId}?alt=media`)).text();
        userStats = JSON.parse(text);
        localStorage.setItem('manhole_collection', JSON.stringify(userStats));
        localStorage.setItem('manhole_drive_backup_hash', driveHash(JSON.stringify(userStats)));
        updateStats();
        renderCollection();
        updatePrefStats();
        updateEditionStats();
        updateDriveStatus();
        alert('復元しました');
    } catch (e) { alert('復元に失敗しました'); }
}

window.addEventListener('load', () => {
    const inp = document.getElementById('driveClientId');
    if (inp && driveClientId()) inp.value = driveClientId();
    updateDriveStatus();
});

function exportBackup() {
    const blob = new Blob([JSON.stringify(userStats, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `manhole_record_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
}

function importBackup(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            userStats = JSON.parse(e.target.result);
            localStorage.setItem('manhole_collection', JSON.stringify(userStats));
            scheduleAutoBackup();
            updateStats();
            renderCollection();
            alert('インポート完了');
        } catch (e) { alert('形式エラー'); }
    };
    reader.readAsText(file);
}

// --- 弾数統計の更新 ---
function updateEditionStats() {
    const grid = document.getElementById('editionStatsGrid');
    if (!grid || masterData.length === 0) return;

    const { edStats, maxEdNum } = computeEditionCounts();

    const sortedEditions = Object.keys(edStats).sort((a, b) => edStats[a].num - edStats[b].num);
    const groups = {};
    sortedEditions.forEach(edStr => {
        const num = edStats[edStr].num;
        const groupIndex = Math.floor((num - 1) / 5);
        const start = groupIndex * 5 + 1;

        let end = (groupIndex + 1) * 5;
        if (end > maxEdNum) end = maxEdNum;

        const groupName = start === end ? `第${start}弾` : `第${start}弾 〜 第${end}弾`;

        if (!groups[groupName]) groups[groupName] = [];
        groups[groupName].push(edStr);
    });

    let html = CORE_CFG.editionStatsHeading ? '<h3 style="margin: 20px 0 10px 10px; font-size: 14px; border-left: 4px solid #4dabff; padding-left: 8px;">弾数別進捗</h3>' : '';

    Object.keys(groups).sort((a, b) => {
        return parseInt(a.replace(/[^0-9]/g, '')) - parseInt(b.replace(/[^0-9]/g, ''));
    }).forEach(groupName => {
        const eds = groups[groupName];
        let gTotal = 0;
        let gCollected = 0;
        let edHtml = '';

        eds.forEach(edStr => {
            const s = edStats[edStr];
            gTotal += s.total;
            gCollected += s.collected;

            const percent = Math.floor((s.collected / s.total) * 100);
            const hue = Math.floor(percent * 1.2);
            const color = s.collected === s.total ? '#ffc107' : `hsl(${hue}, 70%, 50%)`;

            edHtml += `
    <div class="pref-item" onclick="selectEditionFromStats('${edStr}')" style="cursor: pointer;">
        <div class="pref-info"><span>${edStr}</span><span>${s.collected}/${s.total}</span></div>
        <div class="bar-bg">
            <div class="bar-fill" style="width:${percent}%; background-color:${color};"></div>
        </div>
    </div>`;
        });

        const gPercent = Math.floor((gCollected / gTotal) * 100);
        const gColor = gCollected === gTotal ? '#ffc107' : `hsl(${Math.floor(gPercent * 1.2)}, 70%, 50%)`;

        html += `
    <div class="region-container" id="ed-group-${groupName}">
        <div class="region-header" onclick="this.parentElement.classList.toggle('open')">
            <div class="region-info">
                <div class="region-name-row">
                    <span class="arrow">▶</span> ${groupName}
                </div>
                <div class="region-percentage-row">
                    取得率: ${gPercent}% (${gCollected} / ${gTotal})
                </div>
            </div>
            <div class="region-gauge-bg">
                <div class="bar-fill" style="width:${gPercent}%; background-color:${gColor};"></div>
            </div>
        </div>
        <div class="region-content">${edHtml}</div>
    </div>`;
    });

    grid.innerHTML = html;
}

function selectEditionFromStats(edName) {
    const eSel = document.getElementById('editionFilter');
    const sInput = document.getElementById('searchInput');
    if (sInput) sInput.value = "";
    if (eSel) eSel.value = edName;
    handleFilterChange();

    const filterSec = document.getElementById('filterSection');
    if (filterSec) filterSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updatePrefStats() {
    const grid = document.getElementById('prefStatsGrid');
    if (!grid || masterData.length === 0) return;

    const regions = {
        "その他": ["世界", "その他"],
        "北海道": ["北海道"],
        "東北": ["青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"],
        "関東": ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"],
        "北陸": ["新潟県", "富山県", "石川県", "福井県"],
        "中部": ["山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県"],
        "近畿": ["滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"],
        "中国": ["鳥取県", "島根県", "岡山県", "広島県", "山口県"],
        "四国": ["徳島県", "香川県", "愛媛県", "高知県"],
        "九州・沖縄": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]
    };

    const prefStats = computePrefCounts();

    let html = '';

    for (const [regionName, prefs] of Object.entries(regions)) {
        let rTotal = 0;
        let rCollected = 0;
        let prefHtml = '';

        prefs.forEach(pref => {
            const s = prefStats[pref];
            if (!s) return;
            rTotal += s.total;
            rCollected += s.collected;

            const percent = Math.floor((s.collected / s.total) * 100);
            const hue = Math.floor(percent * 1.2);
            const color = s.collected === s.total ? '#ffc107' : `hsl(${hue}, 70%, 50%)`;

            prefHtml += `
    <div class="pref-item" onclick="selectPrefFromStats('${pref}')" style="cursor: pointer;">
        <div class="pref-info"><span>${pref}</span><span>${s.collected}/${s.total}</span></div>
        <div class="bar-bg">
            <div class="bar-fill" style="width:${percent}%; background-color:${color};"></div>
        </div>
    </div>`;
        });

        const rPercent = Math.floor((rCollected / rTotal) * 100);
        const rColor = rCollected === rTotal ? '#ffc107' : `hsl(${Math.floor(rPercent * 1.2)}, 70%, 50%)`;

        html += `
    <div class="region-container" id="reg-${regionName}">
        <div class="region-header" onclick="this.parentElement.classList.toggle('open')">
            <div class="region-info">
                <div class="region-name-row">
                    <span class="arrow">▶</span> ${regionName}
                </div>
                <div class="region-percentage-row">
                    取得率: ${rPercent}% (${rCollected} / ${rTotal})
                </div>
            </div>
            <div class="region-gauge-bg">
                <div class="bar-fill" style="width:${rPercent}%; background-color:${rColor};"></div>
            </div>
        </div>
        <div class="region-content">${prefHtml}</div>
    </div>`;
    }

    grid.innerHTML = html;
}

function selectPrefFromStats(prefName) {
    const pSel = document.getElementById('prefFilter');
    const sInput = document.getElementById('searchInput');
    if (sInput) sInput.value = "";
    if (pSel) pSel.value = prefName;
    handleFilterChange();

    const filterSec = document.getElementById('filterSection');
    if (filterSec) filterSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function celebrate() {
    const colors = ['#4dabff', '#ffc107', '#28a745', '#ffffff'];
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div'); confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + 'vw';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDuration = (Math.random() * 2 + 1) + 's'; confetti.style.opacity = Math.random();
        confetti.style.width = confetti.style.height = (Math.random() * 10 + 5) + 'px';
        document.body.appendChild(confetti); setTimeout(() => confetti.remove(), 3000);
    }
}
