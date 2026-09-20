"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vietnam.travel/vi/things-to-do/3-perfect-days-danang",
    "https://www.vietnam.travel/vi/things-to-do/3-days-hue-culture-seekers",
    "https://vietnam.travel/vi/things-to-do/4-memorable-days-mekong-delta",
    "https://www.vietnam.travel/vi/things-to-do/perfect-weekend-ha-noi",
    "https://vietnam.travel/vi/things-to-do/day-phu-quoc",
    "https://www.vietnam.travel/vi/places-to-go/northern-vietnam/ninh-binh",
    "https://vietnam.travel/vi/node/199",
    "https://vietnam.travel/vi/things-to-do/10-must-try-hanoian-dishes",
    "https://www.vietnam.travel/vi/things-to-do/how-eat-local-hue",
    "https://vietnam.travel/vi/things-to-do/21-must-try-vietnamese-dishes",
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dữ liệu theo contract của Task 2.

    Output:
    {
        "url": str,
        "title": str,
        "date_crawled": str,
        "content_markdown": str,
    }
    """

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )

    markdown_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(
            threshold=0.45,
            threshold_type="fixed",
            min_word_threshold=10,
        ),
        options={
            "ignore_links": False,
        },
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        excluded_tags=[
            "nav",
            "footer",
            "header",
            "script",
            "style",
            "form",
        ],
        word_count_threshold=10,
        markdown_generator=markdown_generator,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config,
        )

    # 1. Kiểm tra crawl có thành công không
    if not result.success:
        raise RuntimeError(
            f"Crawl failed for {url}: "
            f"{result.error_message or 'Unknown error'}"
        )

    # 2. Lấy markdown đã được lọc.
    # Nếu fit_markdown bị rỗng thì fallback về raw_markdown.
    markdown_result = result.markdown

    content = ""

    if markdown_result:
        fit_markdown = getattr(markdown_result, "fit_markdown", None)
        raw_markdown = getattr(markdown_result, "raw_markdown", None)

        if fit_markdown and fit_markdown.strip():
            content = fit_markdown.strip()
        elif raw_markdown and raw_markdown.strip():
            content = raw_markdown.strip()
        elif isinstance(markdown_result, str):
            content = markdown_result.strip()

    # 3. Tránh lưu bài crawl lỗi hoặc gần như rỗng
    if len(content) < 200:
        raise ValueError(
            f"Content too short for {url}: {len(content)} characters"
        )

    # 4. Lấy title từ metadata
    metadata = result.metadata or {}

    if isinstance(metadata, dict):
        title = (
            metadata.get("title")
            or metadata.get("og:title")
            or metadata.get("twitter:title")
            or "Unknown"
        )
    else:
        title = "Unknown"

    title = str(title).strip() or "Unknown"

    # 5. Trả đúng schema mà acceptance test yêu cầu
    return {
        "url": str(result.url or url),
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": content,
    }


async def crawl_all() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)

            output = DATA_DIR / f"article_{index:02d}.json"

            output.write_text(
                json.dumps(
                    article,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            print(
                f"[OK] {index:02d}/{len(ARTICLE_URLS)} "
                f"{article['title']} -> {output.name}"
            )

        except Exception as error:
            print(
                f"[ERROR] {index:02d}/{len(ARTICLE_URLS)} "
                f"{url}\n        {error}"
            )

if __name__ == "__main__":
    asyncio.run(crawl_all())
