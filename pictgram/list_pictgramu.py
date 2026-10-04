import re
from bs4 import BeautifulSoup
import pandas as pd

# 保存したHTMLファイルを読み込み
with open("pictgram/ekikaramanhole_search.html", "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
cards_data = []

# 各カード（class="list"）要素を抽出
for item in soup.find_all("div", class_="list"):
    card_id_elem = item.find("span", class_="card-id")
    if not card_id_elem:
        continue

    # 1. カードIDと管理番号
    full_id = card_id_elem.get_text().strip()
    m_id = re.search(r"([0-9A-Z-]+)(?:\(([^)]+)\))?", full_id)
    card_id = m_id.group(1) if m_id else full_id
    sub_id = m_id.group(2) if m_id and m_id.group(2) else ""
    card_id = re.sub(r"\d+$", "", card_id)

    # 2. 都道府県・自治体・シリーズ
    title_div = item.find("div", class_="card-title")
    pref, city, series = "", "", ""
    if title_div:
        pref_a = title_div.find(
            "a", title=True, href=re.compile(r"search\.cgi\?m=")
        )
        if pref_a:
            pref = pref_a.get_text().strip()

        series_img = title_div.find("img", class_="series")
        if series_img:
            series = series_img.get("title") or series_img.get("alt", "")

        # テキストから自治体名を抽出
        title_text = title_div.get_text()
        tokens = title_text.split()
        if len(tokens) >= 3:
            city = tokens[2]

    # 3. 座標 (10進数)
    lat, lng = "", ""
    map_a = item.find("a", href=re.compile(r"map/\?z="))
    if map_a:
        m_lat = re.search(r"lat=([\d\.]+)", map_a["href"])
        m_lng = re.search(r"lng=([\d\.]+)", map_a["href"])
        if m_lat:
            lat = m_lat.group(1)
        if m_lng:
            lng = m_lng.group(1)

    # 4. ピクトグラム情報
    pict_div = item.find("div", class_="pict")
    pict_summary = []

    if pict_div:
        for span in pict_div.find_all("span", class_="nobr"):
            a_tag = span.find("a")
            img_tag = span.find("img")

            p_code, p_name = "", ""
            if a_tag and "href" in a_tag.attrs:
                m_p = re.search(r"p=(\d+)", a_tag["href"])
                if m_p:
                    p_code = m_p.group(1)

            if img_tag:
                p_name = img_tag.get("title", "")

            # 個数抽出
            count_text = span.get_text().strip()
            m_count = re.search(r"\d+", count_text)
            count = m_count.group(0) if m_count else "1"

            pict_summary.append(f"{p_code}:{p_name}({count})")

    cards_data.append({
        "カードID": card_id,
        "管理番号": sub_id,
        "都道府県": pref,
        "自治体": city,
        "シリーズ": series,
        "緯度": lat,
        "経度": lng,
        "ピクトグラム情報": ", ".join(pict_summary),
    })

# DataFrame化してCSV / Excelに出力
df = pd.DataFrame(cards_data)

# CSV出力（Excelで文字化けしないよう utf-8-sig を指定）
df.to_csv("pictgram_manhole_cards.csv", index=False, encoding="utf-8-sig")

# Excel出力（openpyxlが必要）
# df.to_excel("pictgram/manhole_cards.xlsx", index=False)

print(f"処理完了: {len(df)} 件のデータを抽出しました。")