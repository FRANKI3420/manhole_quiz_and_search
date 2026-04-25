import pandas as pd
import os
import re

def merge_and_rename_manhole():
    if not os.path.exists("manhole_list.csv"):
        print("エラー: manhole_list.csv (既存データ) が見つかりません。")
        return

    df_base = pd.read_csv("manhole_list.csv", encoding="utf-8-sig")
    df_add = pd.read_csv("manhole_list_add.csv", encoding="utf-8-sig")

    # 1. B001が存在する市町村を特定して A001 へ書き換える準備
    b001_targets = set()
    for _, row in df_add.iterrows():
        if "(B001)" in str(row['市町村']):
            base_city_name = row['市町村'].replace("(B001)", "").strip()
            b001_targets.add((row['都道府県'], base_city_name))

    def update_city_name(row):
        if "(" in str(row['市町村']): return row['市町村']
        if (row['都道府県'], row['市町村']) in b001_targets:
            return f"{row['市町村']} (A001)"
        return row['市町村']

    df_base['市町村'] = df_base.apply(update_city_name, axis=1)

    # 2. データの結合
    df_combined = pd.concat([df_base, df_add], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['都道府県', '市町村', '弾数'])

    # 3. 【新機能】並び替え用の作業列を作成
    # 都道府県コード（JIS順）を定義
    pref_order = {
        "北海道": 1, "青森県": 2, "岩手県": 3, "宮城県": 4, "秋田県": 5, "山形県": 6, "福島県": 7,
        "茨城県": 8, "栃木県": 9, "群馬県": 10, "埼玉県": 11, "千葉県": 12, "東京都": 13, "神奈川県": 14,
        "新潟県": 15, "富山県": 16, "石川県": 17, "福井県": 18, "山梨県": 19, "長野県": 20, "岐阜県": 21,
        "静岡県": 22, "愛知県": 23, "三重県": 24, "滋賀県": 25, "京都府": 26, "大阪府": 27, "兵庫県": 28,
        "奈良県": 29, "和歌山県": 30, "鳥取県": 31, "島根県": 32, "岡山県": 33, "広島県": 34, "山口県": 35,
        "徳島県": 36, "香川県": 37, "愛媛県": 38, "高知県": 39, "福岡県": 40, "佐賀県": 41, "長崎県": 42,
        "熊本県": 43, "大分県": 44, "宮崎県": 45, "慶応義塾": 46, "鹿児島県": 46, "沖縄県": 47
    }

    def get_sort_keys(row):
        city = str(row['市町村'])
        # カッコ内の枝番（A001など）を抽出
        match = re.search(r'\((.+)\)', city)
        branch = match.group(1) if match else "000" # 無印は 000 とする
        # カッコを除いた純粋な市町村名
        pure_city = re.sub(r'\(.+\)', '', city).strip()
        
        return pd.Series([
            pref_order.get(row['都道府県'], 99), # 都道府県順
            pure_city,                          # 市町村名順
            branch                              # 枝番順 (A001 < B001)
        ])

    # 作業用列を追加してソート
    df_combined[['_pref_rank', '_city_name', '_branch']] = df_combined.apply(get_sort_keys, axis=1)
    
    # 複数キーでソートを実行
    df_combined = df_combined.sort_values(['_pref_rank', '_city_name', '_branch']).reset_index(drop=True)

    # 4. 作業列を削除して保存
    df_combined = df_combined.drop(columns=['_pref_rank', '_city_name', '_branch'])
    
    df_combined.to_csv("manhole_list.csv", index=False, encoding="utf-8-sig")
    print(f"Step 2 完了: 適切にソートして {len(df_combined)} 件保存しました。")

if __name__ == "__main__":
    merge_and_rename_manhole()