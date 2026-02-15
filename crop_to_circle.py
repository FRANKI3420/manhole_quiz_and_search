from PIL import Image, ImageDraw
import os

def bulk_circle_crop(input_folder, output_folder, center_x, center_y, radius):
    # 1. 保存用フォルダがなければ作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"フォルダを作成しました: {output_folder}")

    # 2. フォルダ内のファイル一覧を取得
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    total_files = len(files)
    print(f"合計 {total_files} 枚の処理を開始します...")

    for i, filename in enumerate(files):
        input_path = os.path.join(input_folder, filename)
        
        # 3. 画像の読み込み
        try:
            img = Image.open(input_path).convert("RGBA")
        except Exception as e:
            print(f"[{i+1}/{total_files}] スキップ (エラー): {filename} - {e}")
            continue

        # 4. 円形マスクの作成
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        
        left_up = (center_x - radius, center_y - radius)
        right_down = (center_x + radius, center_y + radius)
        draw.ellipse([left_up, right_down], fill=255)

        # 5. 切り抜き処理
        result = Image.new("RGBA", img.size, (255, 255, 255, 0))
        result.paste(img, (0, 0), mask=mask)

        # 円の部分だけをクロップ
        crop_box = (center_x - radius, center_y - radius, center_x + radius, center_y + radius)
        final_img = result.crop(crop_box)

        # 6. 保存 (ファイル名は元のまま、拡張子はPNGに変更)
        # ※透過を維持するため、元がjpgでもpngとして保存します
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{name_without_ext}.png")
        
        final_img.save(output_path, "PNG")

        if (i + 1) % 50 == 0:
            print(f"進捗: {i + 1}/{total_files} 枚完了")

    print(f"\nすべて完了しました！ 保存先: {output_folder}")

# --- 設定 ---
INPUT_DIR = "manhole_images"  # 元の画像があるフォルダ
OUTPUT_DIR = "manhole_crops"  # 切り抜き後の保存先フォルダ

# テストで決定した座標
CENTER_X = 257
CENTER_Y = 352
RADIUS = 207

if __name__ == "__main__":
    bulk_circle_crop(INPUT_DIR, OUTPUT_DIR, CENTER_X, CENTER_Y, RADIUS)