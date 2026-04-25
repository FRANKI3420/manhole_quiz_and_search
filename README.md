# マンホールカード類似検索システム：データ更新パイプライン

このプロジェクトは、最新のマンホールカード情報を取得し、画像加工、AI解析、検索インデックス作成までを一気通貫で行うためのデータパイプラインです。



## 📋 ファイル構成と役割

### 1. データ整備フェーズ
| ファイル名 | 役割 | 詳細 |
| :--- | :--- | :--- |
| **`step0_same_check.py`** | **データ整合性検証** | CSV内の重複やファイル名の衝突を事前に検知し、データ欠損を防止する。 |
| **`step2_merge_manhole_csv.py`** | **結合・リネーム** | 既存リストに新規分を合体。B001登場に伴うA001への自動リネームとJIS順ソートを実行。 |

### 2. 画像処理フェーズ
| ファイル名 | 役割 | 詳細 |
| :--- | :--- | :--- |
| **`step3_dl_image_add.py`** | **画像同期 (DL)** | CSVに基づき差分画像のみDL。名前が変わった古い画像は自動削除してクリーンアップ。 |
| **`step4_crop_to_circle_add.py`** | **円形切り抜き** | `manhole_images` から新規分のみを円形に加工。透過PNGとして `manhole_crops` へ保存。 |

### 3. Webアプリ・AI解析フェーズ
| ファイル名 | 役割 | 詳細 |
| :--- | :--- | :--- |
| **`step5_convert_csv_to_master_json.py`** | **JSON変換** | 最終CSVをWebアプリ用JSONに変換。弾数のゼロ埋め（第1弾→第01弾）などの正規化を実施。 |
| **`step6_build_search_index_color_pared.py`** | **AI解析・パレット生成** | AI（ViT）による類似検索インデックス作成と、主要5色のカラーパレット抽出。 |

---

## 🛠 フォルダ構成
- `manhole_images/`: オリジナル画像（JPG/PNG）
- `manhole_crops/`: 加工済み画像（円形透過PNG）
- `manhole_list.csv`: マスターデータリスト
- `master_data.json`: Webアプリ用メインデータ
- `similarity_index.json`: 類似カード紐付けデータ

---

## 🚀 標準運用フロー

新しい弾が追加された際は、以下の順にコマンドを実行してください。

1. **新規リスト作成**: HTML解析等で `manhole_list_add.csv` を用意
2. **整合性チェック**: `python3 step0_same_check.py`
3. **CSV更新**: `python3 step2_merge_manhole_csv.py`
4. **画像DL**: `python3 step3_dl_image_add.py`
5. **画像加工**: `python3 step4_crop_to_circle_add.py`
6. **JSON生成**: `python3 step5_convert_csv_to_master_json.py`
7. **AI解析**: `python3 step6_build_search_index_color_pared.py`

---

## 📝 運用上の注意
- **差分処理**: Step 4 は差分処理モードです。切り抜き設定（座標等）を変更して全件やり直したい場合は、`manhole_crops/` フォルダを一度削除してから実行してください。
- **依存関係**: Step 6 の実行には `torch`, `timm`, `opencv-python`, `scikit-learn` が必要です。