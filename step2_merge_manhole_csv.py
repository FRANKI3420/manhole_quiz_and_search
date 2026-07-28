import pandas as pd
import os
import re

def merge_and_rename_manhole():
    if not os.path.exists("manhole_list.csv"):
        print("エラー: manhole_list.csv (既存データ) が見つかりません。")
        return

    df_base = pd.read_csv("manhole_list.csv", encoding="utf-8-sig")
    
    # manhole_list_add.csv があれば読み込み、なければ空のDFを作成
    if os.path.exists("manhole_list_add.csv"):
        df_add = pd.read_csv("manhole_list_add.csv", encoding="utf-8-sig")
    else:
        df_add = pd.DataFrame(columns=['都道府県', '市町村', '弾数', 'url'])

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

    # 2. データの結合と重複除去
    df_combined = pd.concat([df_base, df_add], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['都道府県', '市町村', '弾数'])

    # 3. 都道府県コード（JIS順）の定義
    pref_order = {
        "北海道": 1, "青森県": 2, "岩手県": 3, "宮城県": 4, "秋田県": 5, "山形県": 6, "福島県": 7,
        "茨城県": 8, "栃木県": 9, "群馬県": 10, "埼玉県": 11, "千葉県": 12, "東京都": 13, "神奈川県": 14,
        "新潟県": 15, "富山県": 16, "石川県": 17, "福井県": 18, "山梨県": 19, "長野県": 20, "岐阜県": 21,
        "静岡県": 22, "愛知県": 23, "三重県": 24, "滋賀県": 25, "京都府": 26, "大阪府": 27, "兵庫県": 28,
        "奈良県": 29, "和歌山県": 30, "鳥取県": 31, "島根県": 32, "岡山県": 33, "広島県": 34, "山口県": 35,
        "徳島県": 36, "香川県": 37, "愛媛県": 38, "高知県": 39, "福岡県": 40, "佐賀県": 41, "長崎県": 42,
        "熊本県": 43, "大分県": 44, "宮崎県": 45, "鹿児島県": 46, "沖縄県": 47, "世界": 98, "その他": 99
    }

    def get_sort_keys(row):
        city = str(row['市町村'])
        match = re.search(r'\((.+)\)', city)
        branch = match.group(1) if match else "000"
        pure_city = re.sub(r'\(.+\)', '', city).strip()
        
        return pd.Series([
            pref_order.get(row['都道府県'], 99),
            pure_city,
            branch
        ])

    df_combined[['_pref_rank', '_city_name', '_branch']] = df_combined.apply(get_sort_keys, axis=1)
    df_combined = df_combined.sort_values(['_pref_rank', '_city_name', '_branch']).reset_index(drop=True)

    # 4. 【ID生成ロジック】ユニークな id を自動生成
    city_counters = {}
    ids = []

    for _, row in df_combined.iterrows():
        pref_code = f"{row['_pref_rank']:02d}"  # 2桁の都道府県コード (例: 27)
        pure_city = row['_city_name']
        branch = row['_branch']
        
        # 枝番が 000（カッコがない場合）は A001 とする
        branch_code = "A001" if branch == "000" else branch

        # 同一都道府県・同一自治体内での通し番号
        pref_city_key = (row['都道府県'], pure_city)
        if pref_city_key not in city_counters:
            city_counters[pref_city_key] = len(city_counters) + 1
        
        city_num = f"{city_counters[pref_city_key]:03d}"  # 3桁の連番

        # IDのフォーマット: 都道府県コード-自治体番号-枝番 (例: 27-005-A001)
        generated_id = f"{pref_code}-{city_num}-{branch_code}"
        ids.append(generated_id)

    # id 列を追加
    df_combined['id'] = ids

    # 5. 不要な作業列を削除し、列順を整理
    df_combined = df_combined.drop(columns=['_pref_rank', '_city_name', '_branch'])
    cols = ['id'] + [c for c in df_combined.columns if c != 'id']
    df_combined = df_combined[cols]

    # 保存
    df_combined.to_csv("manhole_list.csv", index=False, encoding="utf-8-sig")
    print(f"完了: id 列を付与して {len(df_combined)} 件保存しました。")

if __name__ == "__main__":
    merge_and_rename_manhole()