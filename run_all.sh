#!/bin/bash

# エラーが発生したらその時点でスクリプトの実行を停止する
set -e

# Pythonコマンドの指定（環境に合わせて python や python3 に変更してください）
PYTHON_CMD="python"

echo "=========================================="
echo " マンホールデータ処理パイプラインを開始します"
echo "=========================================="

echo "[1/8] Running step00_download_html.py..."
$PYTHON_CMD step00_download_html.py

echo "[2/8] Running step0_same_check.py..."
$PYTHON_CMD step0_same_check.py

echo "[3/8] Running step1_getCardInfo_add.py..."
$PYTHON_CMD step1_getCardInfo_add.py

echo "[4/8] Running step2_merge_manhole_csv.py..."
$PYTHON_CMD step2_merge_manhole_csv.py

echo "[5/8] Running step3_dl_image_add.py..."
$PYTHON_CMD step3_dl_image_add.py

echo "[6/8] Running step4_crop_to_circle_add.py..."
$PYTHON_CMD step4_crop_to_circle_add.py

echo "[7/8] Running step5_convert_csv_to_master_json.py..."
$PYTHON_CMD step5_convert_csv_to_master_json.py

echo "[8/8] Running step6_build_search_index_color_pared.py..."
$PYTHON_CMD step6_build_search_index_color_pared.py

echo "=========================================="
echo " すべての処理が正常に完了しました！"
echo "=========================================="