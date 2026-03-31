import csv
import json
import os
import re

def normalize_edition(text):
    """
    「第1弾」を「第01弾」に変換する関数
    """
    if not text:
        return "不明"
    
    # 正規表現で数字の部分（例: 1）を探す
    match = re.search(r'(\d+)', text)
    if match:
        num = match.group(1)
        # 数字を2桁にゼロパディング（01, 02...）
        # 「第」と「弾」を残して数字だけ置換
        new_num = num.zfill(2)
        return text.replace(num, new_num)
    return text

def convert_csv_to_master_json(input_csv, output_json):
    master_data = []
    
    try:
        with open(input_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 弾数または段数を取得
                raw_edition = row.get("弾数") or row.get("段数") or ""
                # 表記ゆれを修正（第1弾 -> 第01弾）
                edition_value = normalize_edition(raw_edition)
                
                item = {
                    "pref": row.get("都道府県", "その他"),
                    "city": row.get("市町村", "不明"),
                    "url": row.get("画像URL", ""),
                    "edition": edition_value,
                    "id": row.get("市町村", "不明")
                }
                master_data.append(item)
    except FileNotFoundError:
        print(f"エラー: {input_csv} が見つかりません。")
        return

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)

    print(f"完了: {len(master_data)} 件のデータを処理し、弾数を '{edition_value}' 形式に統一しました。")

if __name__ == "__main__":
    INPUT_CSV_FILE = "manhole_list.csv" 
    OUTPUT_JSON_FILE = "master_data.json"
    
    convert_csv_to_master_json(INPUT_CSV_FILE, OUTPUT_JSON_FILE)