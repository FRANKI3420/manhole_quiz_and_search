import os
import json
import numpy as np
import torch
import timm
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

# --- モデル名の修正 ---
# 最新の timm では 'vit_base_patch32_224.openai' もしくは 'vit_base_patch32_clip_224' が一般的です
device = "cpu"
model_name = 'vit_base_patch32_clip_224.openai' # 推奨タグ

print(f"Loading CLIP model via timm on {device}...")

try:
    # モデルの作成を試みる
    model = timm.create_model(model_name, pretrained=True, num_classes=0).to(device)
except RuntimeError:
    # 上記がダメな場合、利用可能なCLIPモデルを検索して再試行
    print(f"Tag '{model_name}' failed. Searching for alternative...")
    avail_models = timm.list_models('*vit_base_patch32*clip*', pretrained=True)
    if not avail_models:
        raise RuntimeError("CLIP model not found. Please run 'pip install timm' update.")
    print(f"Using alternative model: {avail_models[0]}")
    model = timm.create_model(avail_models[0], pretrained=True, num_classes=0).to(device)

model.eval()

# CLIP標準の前処理
data_config = timm.data.resolve_model_data_config(model)
preprocess = timm.data.create_transform(**data_config, is_training=False)

def get_feature(img_path):
    try:
        # 画像を開いてRGB変換
        img = Image.open(img_path).convert("RGB")
        img_input = preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            # 特徴量抽出
            image_features = model(img_input)
            # L2正規化
            image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

# --- 以下メイン処理 ---
crop_dir = "manhole_crops"
if not os.path.exists(crop_dir):
    print(f"Error: Directory '{crop_dir}' not found.")
    exit()

# 画像リスト取得
filenames = [f for f in os.listdir(crop_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
features = []
valid_names = []

print(f"Starting feature extraction for {len(filenames)} images...")

for name in filenames:
    path = os.path.join(crop_dir, name)
    feat = get_feature(path)
    if feat is not None:
        features.append(feat)
        valid_names.append(name)
        if len(valid_names) % 100 == 0:
            print(f"{len(valid_names)} images processed...")

# 類似度計算と保存
if features:
    print("Calculating similarity matrix...")
    features = np.array(features)
    sim_matrix = cosine_similarity(features)

    search_index = {}
    for i, name in enumerate(valid_names):
        # 類似度が高い順にソート（自分以外）
        sim_scores = sorted(list(enumerate(sim_matrix[i])), key=lambda x: x[1], reverse=True)
        # 上位10件を保存
        search_index[name] = [valid_names[idx] for idx, score in sim_scores[1:11]]

    with open("similarity_index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=2)

    print("Done! similarity_index.json created using CLIP.")
else:
    print("No features extracted.")