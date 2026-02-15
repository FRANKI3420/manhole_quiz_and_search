import pandas as pd
from bs4 import BeautifulSoup
import os

def parse_manhole_html(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='shift-jis') as f:
            html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    rows = soup.find_all('tr')
    for row in rows:
        tds = row.find_all('td')
        
        if len(tds) >= 3:
            # --- 修正ポイントここから ---
            # get_text(separator=" ") で <br> をスペースに変換し、
            # .split() と " ".join() で連続する改行や空白を1つのスペースにまとめます
            raw_city_text = tds[0].get_text(separator=" ")
            city_info = " ".join(raw_city_text.split()).strip()
            # --- 修正ポイントここまで ---
            
            img_tag = tds[1].find('img')
            img_url = img_tag['src'] if img_tag else "なし"
            
            edition = tds[2].get_text().strip()
            
            results.append({
                "市町村": city_info,
                "画像URL": img_url,
                "弾数": edition
            })

    df = pd.DataFrame(results)
    df.to_csv("manhole_list.csv", index=False, encoding="utf-8-sig")
    print(f"{len(df)} 件のデータを保存しました（改行除去済み）。")

if __name__ == "__main__":
    parse_manhole_html('input_html.txt') 