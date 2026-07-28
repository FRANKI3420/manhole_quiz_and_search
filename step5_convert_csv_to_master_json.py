import csv
import json
import os
import re
from collections import Counter

def normalize_edition(text):
    """
    「第1弾」を「第01弾」に変換する関数
    """
    if not text:
        return "第00弾"
    
    match = re.search(r'(\d+)', text)
    if match:
        num = match.group(1).zfill(2)
        return f"第{num}弾"
    return text

def convert_csv_to_master_json(input_csv, output_json):
    raw_items = []
    
    try:
        with open(input_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_items.append(row)
    except FileNotFoundError:
        print(f"エラー: {input_csv} が見つかりません。")
        return

    # 1. 市町村ごとの出現回数をカウント（複数種類あるか判別するため）
    base_city_counts = Counter()
    for row in raw_items:
        raw_city = row.get("市町村", "不明")
        base_city = re.sub(r'\s*\([A-Z]\d+\)', '', raw_city).strip()
        base_city_counts[base_city] += 1

    master_data = []
    seen_base_cities = set()

    for row in raw_items:
        raw_city = row.get("市町村", "不明").strip()
        base_city = re.sub(r'\s*\([A-Z]\d+\)', '', raw_city).strip()
        
        raw_edition = row.get("弾数") or row.get("段数") or ""
        edition_value = normalize_edition(raw_edition)
        
        # CSVの固有IDを取得（無い場合は画像URLから安全にフォールバック）
        unique_id = row.get("ID", "").strip()
        if not unique_id and row.get("画像URL"):
            match = re.search(r'(\d{2}-\d{3}-[A-Z0-9]+)', row.get("画像URL", ""))
            if match:
                unique_id = match.group(1)

        # IDが取得できた場合はそれをプライマリIDにし、無ければ市町村名をフォールバックとして使用
        item_id = unique_id if unique_id else raw_city

        item = {
            "id": item_id,                        # 固有ID（例: "27-218-A001"）
            "pref": row.get("都道府県", "その他"),
            "city": raw_city,                     # 市町村表示名（例: "大東市 (A001)"）
            "url": row.get("画像URL", ""),
            "edition": edition_value,
        }

        # 固有IDを追加で明示フィールドとして持たせる（検索・結合用）
        if unique_id:
            item["card_id"] = unique_id

        # 過去データ移行用キー（old_id）の処理
        if base_city_counts[base_city] > 1:
            if base_city not in seen_base_cities:
                item["old_id"] = base_city  # 過去の "大東市" データを救出するためのキー
                seen_base_cities.add(base_city)
            else:
                item["old_id"] = raw_city
        else:
            item["old_id"] = base_city

        master_data.append(item)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)

    print(f"完了: {len(master_data)} 件のデータを処理し、固有IDを組み込んだ JSON を生成しました。")

if __name__ == "__main__":
    INPUT_CSV_FILE = "manhole_list.csv" 
    OUTPUT_JSON_FILE = "master_data.json"
    
    convert_csv_to_master_json(INPUT_CSV_FILE, OUTPUT_JSON_FILE)