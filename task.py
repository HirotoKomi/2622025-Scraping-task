import csv
import time
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


url = 'https://www.musashino-u.ac.jp'
domain = urlparse(url).netloc

# URLを順番に調べるためのリスト
url_list = [url]

# 調べたURLを記録する集合
checked_urls = set()

# URLをキー、ページタイトルを値として保存する辞書
site_map = {}

headers = {
    'User-Agent': 'Mozilla/5.0'
}

while url_list:
    current_url = url_list.pop(0)
    current_url = urldefrag(current_url)[0]

    if current_url in checked_urls:
        continue

    checked_urls.add(current_url)

    # 同一ドメインのページだけを調べる
    if urlparse(current_url).netloc != domain:
        continue

    try:
        res = requests.get(current_url, headers=headers, timeout=20)

        print(f"URL：{current_url}")
        print(f"ステータスコード：{res.status_code}")
        print(f"ステータスメッセージ：{res.reason}")

        # HTTPエラーが発生したページは次へ進む
        res.raise_for_status()

    except requests.RequestException as error:
        print(f"ページを取得できませんでした：{error}")
        continue

    # HTML以外のページは処理しない
    if 'html' not in res.headers.get('Content-Type', '').lower():
        continue

    # HTMLのソースコードをBeautifulSoupオブジェクトに変換する処理
    html_soup = BeautifulSoup(res.content, 'html.parser')
    print(f"html_soupの型：{type(html_soup)}")

    # titleタグからページタイトルを取得する
    title = html_soup.title.get_text(strip=True) if html_soup.title else ''
    site_map[current_url] = title
    print(f"title：{title}")

    # ----- 同一ドメインのリンクを検索する ------- #

    # aタグをすべて取得する
    a_list = html_soup.find_all('a', href=True)

    for a in a_list:
        # 相対URLを絶対URLに変換する
        next_url = urljoin(current_url, a['href'])

        # URL末尾の # 以降を除く
        next_url = urldefrag(next_url)[0]

        # 同一ドメインで、まだ調べていないURLをリストに追加する
        if urlparse(next_url).netloc == domain:
            if next_url not in checked_urls and next_url not in url_list:
                url_list.append(next_url)

    # Webサイトへの負荷を軽減するため、アクセスの間隔をあける
    time.sleep(1)

# ----- URLとtitleをCSVファイルに保存する ------- #

with open('musashino_site_map.csv', 'w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.writer(csv_file)

    # CSVの見出し行
    writer.writerow(['URL', 'title'])

    # URLとtitleを書き込む
    for page_url, page_title in site_map.items():
        writer.writerow([page_url, page_title])

# URLをキー、titleを値とする辞書を表示する
print(site_map)
