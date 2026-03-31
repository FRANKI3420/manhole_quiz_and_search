import os
import shutil
from PIL import Image, ImageDraw

def bulk_circle_crop_with_clean(input_folder, output_folder, center_x, center_y, radius):
    # --- 【追加】出力フォルダのクリーンアップ処理 ---
    if os.path.exists(output_folder):
        print(f"清掃中: {output_folder} 内の古いキャッシュを削除します...")
        # フォルダごと削除して再作成することで、完全に空にする
        shutil.rmtree(output_folder)
    
    os.makedirs(output_folder)
    print(f"フォルダを初期化しました: {output_folder}")
    # --------------------------------------------

    # 1. フォルダ内のファイル一覧を取得
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    total_files = len(files)
    
    if total_files == 0:
        print(f"警告: {input_folder} に画像が見つかりません。Step 3が成功しているか確認してください。")
        return

    print(f"合計 {total_files} 枚の切り抜き処理を開始します...")

    for i, filename in enumerate(files):
        input_path = os.path.join(input_folder, filename)
        
        # 2. 画像の読み込み
        try:
            img = Image.open(input_path).convert("RGBA")
        except Exception as e:
            print(f"[{i+1}/{total_files}] スキップ (エラー): {filename} - {e}")
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

        # 円の部分だけをクロップ
        crop_box = (center_x - radius, center_y - radius, center_x + radius, center_y + radius)
        final_img = result.crop(crop_box)

        # 5. 保存 (ファイル名は元のまま、拡張子はPNGに統一)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{name_without_ext}.png")
        
        final_img.save(output_path, "PNG")

        if (i + 1) % 50 == 0:
            print(f"進捗: {i + 1}/{total_files} 枚完了")

    print(f"\nすべて完了しました！ 最新の画像のみが {output_folder} に保存されています。")

# --- 設定 ---
INPUT_DIR = "manhole_images"  # Step 3で同期されたフォルダ
OUTPUT_DIR = "manhole_crops"  # 切り抜き後の保存先（実行時に空になります）

# 固定座標
CENTER_X = 257
CENTER_Y = 352
RADIUS = 207

if __name__ == "__main__":
    bulk_circle_crop_with_clean(INPUT_DIR, OUTPUT_DIR, CENTER_X, CENTER_Y, RADIUS)