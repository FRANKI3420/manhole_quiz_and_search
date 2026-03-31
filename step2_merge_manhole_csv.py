import pandas as pd

def merge_and_rename_manhole():
    # 1. 各CSVを読み込み
    # 既存データ
    df_base = pd.read_csv("manhole_list.csv", encoding="utf-8-sig")
    # 追加データ
    df_add = pd.read_csv("manhole_list_add.csv", encoding="utf-8-sig")

    # 2. 追加データ側に「(B001)」が含まれる市町村のリストを作成
    # 都道府県と市町村の組み合わせで判定するためセットにする
    b001_targets = set()
    for _, row in df_add.iterrows():
        if "(B001)" in str(row['市町村']):
            # "(B001)" を除いた純粋な市町村名を取得（例：札幌市）
            base_city_name = row['市町村'].replace("(B001)", "").strip()
            b001_targets.add((row['都道府県'], base_city_name))

    print(f"B001検知: {len(b001_targets)} 件の市町村を A001 へ書き換えます。")

    # 3. 既存データ(df_base)の書き換えロジック
    def update_city_name(row):
        pref = row['都道府県']
        city = row['市町村']
        
        # すでに (A001) などが付いている場合はスキップ
        if "(" in str(city):
            return city
            
        # 「都道府県」と「市町村名」が一致し、かつB001が存在する場合
        if (pref, city) in b001_targets:
            return f"{city} (A001)"
        
        return city

    df_base['市町村'] = df_base.apply(update_city_name, axis=1)

    # 4. データの結合 (縦に連結)
    # ignore_index=True でインデックスを振り直す
    df_combined = pd.concat([df_base, df_add], ignore_index=True)

    # 5. 重複削除 (念のため、都道府県・市町村・弾数が完全に一致するものは排除)
    df_combined = df_combined.drop_duplicates(subset=['都道府県', '市町村', '弾数'])

    # 6. 保存
    output_file = "manhole_list.csv"
    df_combined.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    print(f"結合完了: {output_file} に保存しました。")
    print(f"総件数: {len(df_combined)} 件")

if __name__ == "__main__":
    merge_and_rename_manhole()