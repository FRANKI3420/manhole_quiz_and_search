import pandas as pd
from bs4 import BeautifulSoup
import re

def parse_manhole_html_v2(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='shift-jis') as f:
            html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # 全ての行を取得
    rows = soup.find_all('tr')
    
    for row in rows:
        tds = row.find_all('td')
        
        # 標準的な行は <td> が 7つ（またはそれ以上）あります
        # 市町村(0), 画像(1), 弾数(2), 日付(3), 配布場所(4), 配布時間(5), 在庫(6)
        if len(tds) >= 5:
            # 1. 市町村のクリーンアップ
            raw_city_text = tds[0].get_text(separator=" ")
            city_info = " ".join(raw_city_text.split()).strip()
            
            # 2. 配布場所と住所の抽出
            # 配布場所のセル(tds[4])を改行で分割してリスト化
            location_cell = tds[4]
            lines = [line.strip() for line in location_cell.get_text(separator="\n").split("\n") if line.strip()]
            
            # 1行目を配布場所名、2行目を住所と仮定（データがない場合は"不明"）
            dist_place = lines[0] if len(lines) > 0 else "不明"
            address = lines[1] if len(lines) > 1 else "住所情報なし"
            
            # 3. 都道府県の抽出（住所の先頭から）
            # 日本の都道府県名パターンにマッチさせる
            pref_match = re.match(r'^(東京都|道府県|.{2,3}県|北海道)', address)
            pref = pref_match.group(1) if pref_match else "不明"

            # 4. その他既存データ
            img_tag = tds[1].find('img')
            img_url = img_tag['src'] if img_tag else "なし"
            edition = tds[2].get_text().strip()

            results.append({
                "都道府県": pref,
                "市町村": city_info,
                "配布場所": dist_place,
                "住所": address,
                "弾数": edition,
                "画像URL": img_url
            })

    # テスト用の別ファイルに出力
    output_file = "manhole_test_output.csv"
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"テスト出力完了: {len(df)} 件のデータを '{output_file}' に保存しました。")

if __name__ == "__main__":
    # 入力ファイル名は適宜変更してください
    parse_manhole_html_v2('input_html.txt')