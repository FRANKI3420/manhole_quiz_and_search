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
    # ※ CSV側で「市町村」列にベース名（大東市）が入っている場合、またはすでに(A001)がついている場合を考慮
    base_city_counts = Counter()
    for row in raw_items:
        raw_city = row.get("市町村", "不明")
        # "(A001)" などが付いている場合は取り除いてベースの市町村名を取得
        base_city = re.sub(r'\s*\([A-Z]\d+\)', '', raw_city).strip()
        base_city_counts[base_city] += 1

    master_data = []
    seen_base_cities = set()

    for row in raw_items:
        raw_city = row.get("市町村", "不明")
        base_city = re.sub(r'\s*\([A-Z]\d+\)', '', raw_city).strip()
        
        raw_edition = row.get("弾数") or row.get("段数") or ""
        edition_value = normalize_edition(raw_edition)
        
        # 現在のID（例: "大東市 (A001)" または "大東市"）
        current_id = raw_city.strip()

        item = {
            "id": current_id,
            "pref": row.get("都道府県", "その他"),
            "city": current_id,
            "url": row.get("画像URL", ""),
            "edition": edition_value,
        }

        # 【重要】パターン1の核心部分
        # もし複数種類ある市町村で、かつ「最初に出てきた1種目」であれば、
        # 過去のユーザーデータ参照用キーとして旧表記（例: "大東市"）を 'old_id' または 'alias' に記録
        if base_city_counts[base_city] > 1:
            if base_city not in seen_base_cities:
                item["old_id"] = base_city  # 過去の "大東市" データを救出するためのキー
                seen_base_cities.add(base_city)
        else:
            # 1種類しかない場合は、そのまま
            item["old_id"] = current_id

        master_data.append(item)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)

    print(f"完了: {len(master_data)} 件のデータを処理し、旧データ引き継ぎ用キー(old_id)を付与しました。")

if __name__ == "__main__":
    INPUT_CSV_FILE = "manhole_list.csv" 
    OUTPUT_JSON_FILE = "master_data.json"
    
    convert_csv_to_master_json(INPUT_CSV_FILE, OUTPUT_JSON_FILE)