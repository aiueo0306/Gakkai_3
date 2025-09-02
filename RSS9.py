import os
import sys
import subprocess
import tempfile
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ===== GitHub 上の共通関数を一時ディレクトリにクローン =====
REPO_URL = "https://github.com/aiueo0306/shared-python-env.git"
SHARED_DIR = os.path.join(tempfile.gettempdir(), "shared-python-env")

if not os.path.exists(SHARED_DIR):
    print("🔄 共通関数を初回クローン中...")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, SHARED_DIR], check=True)
else:
    print("🔁 共通関数を更新中...")
    subprocess.run(["git", "-C", SHARED_DIR, "pull"], check=True)

sys.path.append(SHARED_DIR)

# ===== 共通関数のインポート =====
from rss_utils import generate_rss
from scraper_utils import extract_items

# ===== 固定情報（学会サイト） =====
BASE_URL = "http://www.praj.jp/topics/list.php"
GAKKAI = "日本小児リウマチ学会"

SELECTOR_TITLE = "div.topics li"
title_selector = "a"
title_index = 0
href_selector = "a"
href_index = 0
SELECTOR_DATE = "div.topics li"
date_selector = "span"
date_index = 0
year_unit = "年"
month_unit = "月"
day_unit = "日"
date_format = f"%Y{year_unit}%m{month_unit}%d{day_unit}"
date_regex = rf"(\d{{2,4}})\s*{year_unit}\s*(\d{{1,2}})\s*{month_unit}\s*(\d{{1,2}})\s*{day_unit}"

# ===== Playwright 実行ブロック =====
with sync_playwright() as p:
    print("▶ ブラウザを起動中...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        print("▶ ページにアクセス中...")
        page.goto(BASE_URL, timeout=120000)
        try:
            page.wait_for_load_state("networkidle", timeout=120000)
        except Exception:
            page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("load", timeout=30000)
    except TimeoutError as e:
        print("⚠ ページの読み込みに失敗しました。")
        browser.close()
        exit()

    print("▶ 記事を抽出しています...")
    items = extract_items(
        page,
        SELECTOR_DATE,
        SELECTOR_TITLE,
        title_selector,
        title_index,
        href_selector,
        href_index,
        BASE_URL,
        date_selector,
        date_index,
        date_format,
        date_regex,
    )

    if not items:
        print("⚠ 抽出できた記事がありません。HTML構造が変わっている可能性があります。")

    os.makedirs("rss_output", exist_ok=True)
    rss_path = "rss_output/Feed9.xml"
    generate_rss(items, rss_path, BASE_URL, GAKKAI)
    browser.close()