import os
import json
import numpy as np
import torch
import timm
import cv2  # 追加
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

# --- 設定 ---
device = "cpu"
model_name = 'vit_base_patch32_clip_224.openai' 
crop_dir = "manhole_crops"
master_data_path = "master_data.json" # すでにデータがある場合はそれを読み込み、パレットを追記します

# 1. CLIPモデルのロード (前回と同じ)
print(f"Loading CLIP model on {device}...")
try:
    model = timm.create_model(model_name, pretrained=True, num_classes=0).to(device)
except:
    avail_models = timm.list_models('*vit_base_patch32*clip*', pretrained=True)
    model = timm.create_model(avail_models[0], pretrained=True, num_classes=0).to(device)
model.eval()

data_config = timm.data.resolve_model_data_config(model)
preprocess = timm.data.create_transform(**data_config, is_training=False)

# --- 2. カラーパレット抽出関数 (K-Means法) ---
def get_color_palette(img_path, num_colors=5):
    try:
        # OpenCVで読み込み
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (100, 100)) # 高速化のため縮小
        
        pixels = img.reshape((-1, 3)).astype(np.float32)
        
        # K-Means実行
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        counts = np.bincount(labels.flatten())
        total = counts.sum()
        
        palette = []
        for i, center in enumerate(centers):
            hex_color = "#{:02x}{:02x}{:02x}".format(int(center[0]), int(center[1]), int(center[2]))
            palette.append({
                "hex": hex_color,
                "ratio": round((counts[i] / total) * 100, 1)
            })
        
        # 割合の多い順にソート
        return sorted(palette, key=lambda x: x['ratio'], reverse=True)
    except:
        return []

# --- 3. メイン処理 ---
filenames = [f for f in os.listdir(crop_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
features = []
valid_names = []
palette_dict = {} # ファイル名をキーにしてパレットを保存

print(f"Extracting CLIP features and Color Palettes for {len(filenames)} images...")

for name in filenames:
    path = os.path.join(crop_dir, name)
    
    # CLIP特徴抽出
    try:
        img_pil = Image.open(path).convert("RGB")
        img_input = preprocess(img_pil).unsqueeze(0).to(device)
        with torch.no_grad():
            feat = model(img_input)
            feat /= feat.norm(dim=-1, keepdim=True)
            features.append(feat.cpu().numpy()[0])
            valid_names.append(name)
    except Exception as e:
        print(f"CLIP Error {name}: {e}")
        continue
    
    # カラーパレット抽出
    palette_dict[name] = get_color_palette(path)
    
    if len(valid_names) % 100 == 0:
        print(f"{len(valid_names)} cards processed...")

# --- 4. 類似度インデックスの保存 ---
print("Saving similarity_index.json...")
sim_matrix = cosine_similarity(np.array(features))
search_index = {}
for i, name in enumerate(valid_names):
    sim_scores = sorted(list(enumerate(sim_matrix[i])), key=lambda x: x[1], reverse=True)
    search_index[name] = [valid_names[idx] for idx, score in sim_scores[1:11]]

with open("similarity_index.json", "w", encoding="utf-8") as f:
    json.dump(search_index, f, ensure_ascii=False, indent=2)

# --- 5. master_data.json の更新（重要！） ---
print("Updating master_data.json with color palettes...")
if os.path.exists(master_data_path):
    with open(master_data_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)
    
    # 各データにパレットを紐付け
    for item in master_data:
        # ファイル名（例：廿日市市.png）がパレット辞書にあれば追加
        filename = item.get("city") + ".png" # もしURLから判断する場合は適宜修正
        if filename in palette_dict:
            item["palette"] = palette_dict[filename]
    
    with open(master_data_path, "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)

print("Done! All processing complete.")