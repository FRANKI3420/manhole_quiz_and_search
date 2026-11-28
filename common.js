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
