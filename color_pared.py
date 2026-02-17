import cv2
import numpy as np
import json
import os

def get_color_palette(img_path, num_colors=5):
    # 画像を読み込み（OpenCV）
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 処理高速化のためにリサイズ
    img = cv2.resize(img, (100, 100))
    
    # ピクセルデータを1列に並べる
    pixels = img.reshape((-1, 3)).astype(np.float32)
    
    # K-Means法で代表色を抽出
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # 各色が画像内で占める割合を計算
    counts = np.bincount(labels.flatten())
    total = counts.sum()
    
    palette = []
    for i, center in enumerate(centers):
        # 16進数カラーコードに変換
        hex_color = "#{:02x}{:02x}{:02x}".format(int(center[0]), int(center[1]), int(center[2]))
        # 割合(%)
        percentage = (counts[i] / total) * 100
        palette.append({"hex": hex_color, "ratio": round(percentage, 1)})
        
    # 占有率が高い順にソート
    palette = sorted(palette, key=lambda x: x['ratio'], reverse=True)
    return palette

# master_data.jsonを更新するイメージで回す
# results[city_name] = get_color_palette(path)