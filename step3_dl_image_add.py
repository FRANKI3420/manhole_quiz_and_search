import csv
import urllib.request
import os
import time

def sync_manhole_images(csv_file):
    save_dir = "manhole_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 1. CSVから「あるべきファイル名」のリストを作成
    expected_files = set()
    download_list = []

    with open(csv_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            city_name = row['市町村'].replace('/', '_').replace(':', '：')
            img_url = row['画像URL']
            if not img_url.startswith("http"):
                continue
            
            ext = os.path.splitext(img_url)[1]
            file_name = f"{city_name}{ext}"
            
            expected_files.add(file_name)
            download_list.append({"url": img_url, "file_name": file_name})

    # 2. 不要な画像（名前が変わった古い画像など）を削除
    print("不要なファイルのクリーンアップを開始します...")
    current_files = os.listdir(save_dir)
    for f in current_files:
        if f not in expected_files:
            os.remove(os.path.join(save_dir, f))
            print(f"削除しました (旧名/不要): {f}")

    # 3. 差分（新しいカード、リネームされたカード）のみダウンロード
    print("\n新規・差分ダウンロードを開始します...")
    for i, item in enumerate(download_list):
        save_path = os.path.join(save_dir, item["file_name"])

        # すでに存在する場合はスキップ（差分のみ処理）
        if os.path.exists(save_path):
            continue

        try:
            with urllib.request.urlopen(item["url"]) as response:
                with open(save_path, 'wb') as out_file:
                    out_file.write(response.read())
            
            print(f"新着保存: {item['file_name']}")
            time.sleep(0.5) # サーバー負荷軽減
            
        except Exception as e:
            print(f"失敗: {item['file_name']} - {e}")

    print("\n同期が完了しました。")

if __name__ == "__main__":
    sync_manhole_images("manhole_list.csv")