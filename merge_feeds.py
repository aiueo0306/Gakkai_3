import feedparser
from feedgen.feed import FeedGenerator
from glob import glob

fg = FeedGenerator()
fg.title('統合RSSフィード')
fg.link(href='https://example.com/rss_output/combined.xml', rel='self')
fg.description('複数フィードを統合したマスターRSS')
fg.language('ja')

# すべてのxmlを対象
for xml_file in glob('rss_output/*.xml'):
    d = feedparser.parse(xml_file)
    source = d.feed.get("title", xml_file)

    for entry in d.entries:
        fe = fg.add_entry()
        fe.title(f"[{source}] {entry.title}")
        fe.link(href=entry.link)
        fe.description(entry.get("summary", ""))
        fe.pubDate(entry.get("published", ""))
        fe.guid(entry.link + "#" + entry.get("published", "2025"))

fg.rss_file('rss_output/combined.xml')
