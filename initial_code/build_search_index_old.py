import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity

# 1. モデルの準備 (特徴抽出用に最後の層を除いたMobileNetV2)
model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

def get_feature(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return model.predict(x, verbose=0)[0]

# 2. 全画像の特徴を計算
crop_dir = "manhole_crops"
filenames = [f for f in os.listdir(crop_dir) if f.endswith(".png")]
features = []
valid_names = []

print(f"{len(filenames)} 枚の特徴を抽出中...")
for name in filenames:
    try:
        path = os.path.join(crop_dir, name)
        features.append(get_feature(path))
        valid_names.append(name)
    except:
        continue

# 3. 類似度（コサイン類似度）を全ペアで計算
print("類似度行列を計算中...")
features = np.array(features)
sim_matrix = cosine_similarity(features)

# 4. 各画像に対し、似ている順位TOP10を抽出して辞書化
search_index = {}
for i, name in enumerate(valid_names):
    # 自分自身を除いて、似ている順にソート
    sim_scores = list(enumerate(sim_matrix[i]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # 上位10件のファイル名を保存（1番目は自分なので[1:11]）
    top_matches = [valid_names[idx] for idx, score in sim_scores[1:11]]
    search_index[name] = top_matches

# 5. JSONとして保存
with open("similarity_index.json", "w", encoding="utf-8") as f:
    json.dump(search_index, f, ensure_ascii=False, indent=2)

print("完了！ similarity_index.json を作成しました。")