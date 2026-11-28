// common.js — 全ページ共通のデータ層（記録の読み込み・所持判定・統計の折り畳み）
// 各ページは事前に userStats（localStorageの内容）をグローバルに用意すること。
// ※ localStorage のキーと保存形式は変更しない。

// カードの所持状態を「ID優先」で取得する。
// 1. ID単体(card.id) -> 2. ID付き旧キー(city (id)) -> 3. 市区町村名のみ の順で検索
function getCardStat(card) {
    if (!card) return null;
    const fullKey = `${card.city} (${card.id})`;
    return userStats[card.id] || userStats[fullKey] || userStats[card.city] || null;
}

// 統計セクションの開閉トグル
function toggleStatsSection(id, btn) {
    const el = document.getElementById(id);
    if (!el) return;
    const isOpen = el.style.display !== 'none';
    el.style.display = isOpen ? 'none' : '';
    if (btn) btn.textContent = isOpen ? '開く ▼' : '閉じる ▲';
}

// 記録キー（またはレコード内の id）がカードに対応するか判定する（カレンダー等のキー照合用）
function statKeyMatchesCard(key, stat, card) {
    if (!card) return false;
    const fullKey = `${card.city} (${card.id})`;
    return key === fullKey || key === card.city || key === card.id ||
        !!(stat && (stat.id === fullKey || stat.id === card.id));
}

// 都道府県別の総数・取得数を集計する
function computePrefCounts() {
    const prefStats = {};
    masterData.forEach(card => {
        if (!prefStats[card.pref]) prefStats[card.pref] = { total: 0, collected: 0 };
        prefStats[card.pref].total++;
        if (getCardStat(card)?.collected) prefStats[card.pref].collected++;
    });
    return prefStats;
}

// 弾数別の総数・取得数を集計する（最大の弾番号も返す）
function computeEditionCounts() {
    const edStats = {};
    let maxEdNum = 0;
    masterData.forEach(card => {
        const edNum = parseInt(card.edition.replace(/[^0-9]/g, ''));
        if (isNaN(edNum)) return;
        if (edNum > maxEdNum) maxEdNum = edNum;
        const edStr = card.edition;
        if (!edStats[edStr]) edStats[edStr] = { total: 0, collected: 0, num: edNum };
        edStats[edStr].total++;
        if (getCardStat(card)?.collected) edStats[edStr].collected++;
    });
    return { edStats, maxEdNum };
}
