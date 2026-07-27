import requests
from bs4 import BeautifulSoup

# 1. サイトのHTMLを取得
url = "https://www.gk-p.jp/mhcard/?pref=zenkoku#mhcard_result"
response = requests.get(url)
response.encoding = response.apparent_encoding

# 2. BeautifulSoupでHTMLを解析
soup = BeautifulSoup(response.text, "html.parser")

# 3. 抽出したい「弾」を指定
target_bullet = "第29弾"

# 4. 条件に合う <tr>（行）の文字列を格納するリスト
extracted_rows = []

# すべての <tr> タグをループ処理
for tr in soup.find_all("tr"):
    # <tr> の中に指定した文字列が含まれているか確認
    if target_bullet in tr.get_text():
        # タグとその中身をそのまま文字列として取得
        extracted_rows.append(str(tr))

# 5. 抽出した <tr> の塊をそのまま改行で結合
output_text = "\n".join(extracted_rows)

# 6. ファイルに保存
filename = f"manhole_cards_{target_bullet}.txt"  # プレーンなテキストとして保存
with open(filename, mode="w", encoding="utf-8") as f:
    f.write(output_text)

print(f"「{target_bullet}」の<tr>要素のみを『{filename}』に保存しました！")