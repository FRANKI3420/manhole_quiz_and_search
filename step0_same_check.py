import pandas as pd
import os

def detect_manhole_duplicates(csv_file):
    df = pd.read_csv(csv_file, encoding="utf-8-sig")
    
    print(f"検証開始: 全 {len(df)} 件のデータをチェックします...\n")

    # 1. 行レベルの完全重複チェック
    duplicate_rows = df[df.duplicated(keep=False)]
    if not duplicate_rows.empty:
        print(f"【警告】CSV内に全く同じ内容の行が {len(duplicate_rows)} 件あります:")
        print(duplicate_rows[['都道府県', '市町村', '弾数']])
        print("-" * 30)

    # 2. 保存ファイル名の衝突チェック
    # (Step 3のロジックをシミュレート)
    def get_filename(row):
        city = str(row['市町村']).replace('/', '_').replace(':', '：')
        ext = os.path.splitext(str(row['画像URL']))[1]
        return f"{city}{ext}"

    df['generated_filename'] = df.apply(get_filename, axis=1)
    
    # ファイル名で重複をカウント
    fn_counts = df['generated_filename'].value_counts()
    conflicts = fn_counts[fn_counts > 1]

    if not conflicts.empty:
        print(f"【重要】保存ファイル名が衝突しているデータが {len(conflicts)} 種類（計 {conflicts.sum()} 行）あります。")
        print("これが原因でダウンロード数が減っています：")
        for filename, count in conflicts.items():
            conflict_data = df[df['generated_filename'] == filename]
            print(f"\nファイル名: {filename} ({count}件がこの名前になります)")
            # どの行が衝突しているか表示
            print(conflict_data[['都道府県', '市町村', '弾数', '画像URL']])
    else:
        print("ファイル名の衝突は見つかりませんでした。")

    # 3. 数学的整合性チェック
    unique_files = df['generated_filename'].nunique()
    print(f"\n--- 最終集計 ---")
    print(f"CSV総行数: {len(df)}")
    print(f"生成されるユニークなファイル数: {unique_files}")
    print(f"不足分: {len(df) - unique_files} 件 (これらが上書きまたはスキップされています)")

if __name__ == "__main__":
    # ファイル名は自分の環境に合わせて変えてください
    detect_manhole_duplicates("manhole_list.csv")