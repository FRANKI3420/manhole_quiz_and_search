import csv
import json
import re

# 1. CSVファイルからカードIDごとのピクトグラムタグを抽出
pictgram_map = {}

with open('pictgram_manhole_cards.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        card_id = row.get('カードID', '').strip()
        pict_info = row.get('ピクトグラム情報', '').strip()
        
        if not card_id or not pict_info:
            continue
        
        # 正規表現で ":名称(" のパターンから「名称」部分のみを抽出
        # 例: "015:スポーツ(1), 029:川(1)" -> ['スポーツ', '川']
        tags = re.findall(r':([^(]+)\(', pict_info)
        
        if tags:
            if card_id not in pictgram_map:
                pictgram_map[card_id] = set()
            pictgram_map[card_id].update(tags)

# 2. master_data.json を読み込み
with open('master_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 3. master_data の各カードにタグを追加
updated_card_count = 0
added_tag_count = 0

for item in data:
    # tags キーが存在しない場合は空配列で初期化
    if "tags" not in item or not isinstance(item["tags"], list):
        item["tags"] = []

    card_id = item.get("card_id")
    
    # CSV内に該当する card_id がある場合
    if card_id in pictgram_map:
        card_updated = False
        for tag in pictgram_map[card_id]:
            # 重複していないタグのみ追加（既存の「ガンダム」等のタグは保持）
            if tag not in item["tags"]:
                item["tags"].append(tag)
                added_tag_count += 1
                card_updated = True
        
        if card_updated:
            updated_card_count += 1

# 4. master_data.json に上書き保存
with open('master_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("--- 処理完了 ---")
print(f"更新されたカード数: {updated_card_count} 件")
print(f"追加されたピクトグラムタグ総数: {added_tag_count} 個")