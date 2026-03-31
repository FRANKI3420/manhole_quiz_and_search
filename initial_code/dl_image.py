import csv
import urllib.request
import os
import time

def download_images_standard(csv_file):
    save_dir = "manhole_images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"ダウンロードを開始します...")

    with open(csv_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            img_url = row['画像URL']
            # ファイル名に使えない文字を置換
            city_name = row['市町村'].replace('/', '_').replace(':', '：')
            
            if not img_url.startswith("http"):
                continue

            # 拡張子を取得し、保存パスを作成
            ext = os.path.splitext(img_url)[1]
            file_name = f"{city_name}{ext}"
            save_path = os.path.join(save_dir, file_name)

            # 重複チェック
            if os.path.exists(save_path):
                continue

            try:
                # 標準ライブラリ urllib を使用
                with urllib.request.urlopen(img_url) as response:
                    with open(save_path, 'wb') as out_file:
                        out_file.write(response.read())
                
                print(f"[{i+1}] 保存完了: {file_name}")
                
                # 負荷軽減のための待機
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[{i+1}] 失敗: {city_name} - {e}")

    print("\nすべての処理が完了しました。")

if __name__ == "__main__":
    download_images_standard("manhole_list.csv")