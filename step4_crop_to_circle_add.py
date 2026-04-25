import os
from PIL import Image, ImageDraw

def bulk_circle_crop_incremental(input_folder, output_folder, center_x, center_y, radius):
    # --- フォルダの準備（削除はせず、存在確認のみ） ---
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"新規フォルダを作成しました: {output_folder}")
    else:
        print(f"既存のフォルダを利用します（差分のみ処理）: {output_folder}")

    # 1. フォルダ内のファイル一覧を取得
    all_entries = os.listdir(input_folder)
    image_extensions = ('.jpg', '.jpeg', '.png')
    files = [f for f in all_entries if f.lower().endswith(image_extensions)]
    
    total_files = len(files)
    process_count = 0  # 実際に処理する数
    skip_count = 0     # スキップする数

    print(f"合計 {total_files} 枚のチェックを開始します...")

    for i, filename in enumerate(files):
        # 保存予定のパスを確認
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{name_without_ext}.png")

        # --- 【重要】差分チェック：既に出力ファイルがあればスキップ ---
        if os.path.exists(output_path):
            skip_count += 1
            continue

        input_path = os.path.join(input_folder, filename)
        
        # 2. 画像の読み込み
        try:
            img = Image.open(input_path).convert("RGBA")
        except Exception as e:
            print(f"[{i+1}/{total_files}] エラー: {filename} - {e}")
            continue

        # 3. 円形マスクの作成
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        left_up = (center_x - radius, center_y - radius)
        right_down = (center_x + radius, center_y + radius)
        draw.ellipse([left_up, right_down], fill=255)

        # 4. 切り抜き処理
        result = Image.new("RGBA", img.size, (255, 255, 255, 0))
        result.paste(img, (0, 0), mask=mask)
        crop_box = (center_x - radius, center_y - radius, center_x + radius, center_y + radius)
        final_img = result.crop(crop_box)

        # 5. 保存
        final_img.save(output_path, "PNG")
        process_count += 1

        if process_count % 50 == 0:
            print(f"進捗: {process_count} 枚の新規切り抜き完了...")

    print(f"\n--- 処理結果 ---")
    print(f"総ファイル数: {total_files} 件")
    print(f"スキップ（既存）: {skip_count} 件")
    print(f"新規切り抜き完了: {process_count} 件")
    print(f"出力先: {output_folder}")

# --- 設定 ---
INPUT_DIR = "manhole_images"
OUTPUT_DIR = "manhole_crops"

CENTER_X = 257
CENTER_Y = 352
RADIUS = 207

if __name__ == "__main__":
    bulk_circle_crop_incremental(INPUT_DIR, OUTPUT_DIR, CENTER_X, CENTER_Y, RADIUS)