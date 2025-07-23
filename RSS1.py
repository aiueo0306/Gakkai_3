from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# === 学会情報 ===
BASE_URL = "https://www.jnss.org/"
DEFAULT_LINK = "https://www.jnss.org/news-topics"
ORG_NAME = "日本神経科学学会"

def generate_rss(items, output_path):
    fg = FeedGenerator()
    fg.title(f"{ORG_NAME}トピックス")
    fg.link(href=DEFAULT_LINK)
    fg.description(f"{ORG_NAME}の最新トピック情報")
    fg.language("ja")
    fg.generator("python-feedgen")
    fg.docs("http://www.rssboard.org/rss-specification")
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in items:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.description(item['description'])
        guid_value = f"{item['link']}#{item['pub_date'].strftime('%Y%m%d')}"
        entry.guid(guid_value, permalink=False)
        entry.pubDate(item['pub_date'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fg.rss_file(output_path)
    print(f"\n✅ RSSフィード生成完了！📄 保存先: {output_path}")


def extract_items(page):
    selector = "table.righttbl tr"
    rows = page.locator(selector)
    count = rows.count()
    print(f"📦 発見した記事数: {count}")
    items = []

    max_items = 10
    for i in range(min(count, max_items)):
        try:
            row = rows.nth(i)

            # 🔗 aタグからタイトルとリンク取得
            a_tag = row.locator("td a")
            title = a_tag.inner_text().strip()
            href = a_tag.get_attribute("href")
            full_link = urljoin(BASE_URL, href)

            # 📅 th内テキストから日付を抽出（画像を除いてテキスト部分のみ）
            th_text = row.locator("th").inner_text().strip()
            match = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", th_text)
            if not match:
                raise ValueError(f"日付形式が不明: {th_text}")
            year, month, day = map(int, match.groups())
            pub_date = datetime(year, month, day, tzinfo=timezone.utc)

            items.append({
                "title": title,
                "link": full_link,
                "description": title,
                "pub_date": pub_date
            })

        except Exception as e:
            print(f"⚠ 行{i+1}の解析に失敗: {e}")
            continue

    return items



# ===== 実行ブロック =====
with sync_playwright() as p:
    print("▶ ブラウザを起動中...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("▶ ページにアクセス中...")
        page.goto(DEFAULT_LINK, timeout=30000)
        page.wait_for_load_state("load", timeout=30000)
    except PlaywrightTimeoutError:
        print("⚠ ページの読み込みに失敗しました。")
        browser.close()
        exit()

    print("▶ 記事を抽出しています...")
    items = extract_items(page)

    if not items:
        print("⚠ 抽出できた記事がありません。HTML構造が変わっている可能性があります。")

    rss_path = "rss_output/Feed1.xml"
    generate_rss(items, rss_path)
    browser.close()
