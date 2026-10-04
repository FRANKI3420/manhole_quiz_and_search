import requests

url = "https://ekikaramanhole.whitebeach.org/ext/manholecard/search.cgi?r=0&s=0&p=0"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # 自動識別またはUTF-8を設定して文字化けを防止
    response.encoding = response.apparent_encoding or 'utf-8'

    # ファイルに保存
    with open("ekikaramanhole_search.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    print("HTMLの取得に成功しました。『ekikaramanhole_search.html』に保存しました。")

except requests.exceptions.RequestException as e:
    print(f"取得エラーが発生しました: {e}")