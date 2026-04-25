import pandas as pd
from bs4 import BeautifulSoup
import re

def parse_manhole_html(file_path):
    # 都道府県コードマップ
    pref_map = {
        "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
        "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
        "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
        "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
        "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
        "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
        "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
        "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
        "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
        "46": "鹿児島県", "47": "沖縄県"
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except:
        with open(file_path, 'r', encoding='shift-jis') as f:
            html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    for row in soup.find_all('tr'):
        tds = row.find_all('td')
        if len(tds) >= 3:
            raw_city_text = tds[0].get_text(separator=" ")
            city_info = " ".join(raw_city_text.split()).strip()
            
            img_tag = tds[1].find('img')
            img_url = img_tag['src'] if img_tag else "なし"
            edition = tds[2].get_text().strip()
            
            # URLから都道府県を推測
            pref_name = "その他"
            if img_url != "なし":
                match = re.search(r'/mhc/(\d{2})-', img_url)
                if match and match.group(1) in pref_map:
                    pref_name = pref_map[match.group(1)]

            results.append({
                "都道府県": pref_name,
                "市町村": city_info,
                "画像URL": img_url,
                "弾数": edition
            })

    df = pd.DataFrame(results)
    df.to_csv("manhole_list_add.csv", index=False, encoding="utf-8-sig")
    print(f"Step 1 完了: {len(df)} 件のデータを保存しました。")

if __name__ == "__main__":
    parse_manhole_html('input_html.txt')