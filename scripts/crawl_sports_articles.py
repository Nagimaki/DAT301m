#!/usr/bin/env python3
"""Crawl Vietnamese sports news articles (full text) into CSV.

Usage:
  python scripts/crawl_sports_articles.py --output du_lieu_the_thao_vi_500_bai.csv --limit 500
"""

from __future__ import annotations

import argparse
import csv
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"

LISTING_URLS = [
    "https://vnexpress.net/the-thao",
    "https://vnexpress.net/the-thao/tennis",
    "https://vnexpress.net/the-thao/golf",
    "https://vnexpress.net/the-thao/hau-truong",
    "https://vnexpress.net/the-thao/cac-mon-khac",
    "https://vnexpress.net/the-thao/bong-ro",
    "https://vnexpress.net/the-thao/dua-xe",
]


@dataclass
class Article:
    title: str
    url: str
    published_at: str
    body: str
    source: str = "VnExpress"


def fetch_text(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def clean_html_text(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def extract_article_links(listing_html: str) -> list[str]:
    links = re.findall(r'href="(https://vnexpress\.net/[^"]+?\.html)"', listing_html)
    out: list[str] = []
    seen: set[str] = set()
    for link in links:
        if any(x in link for x in ("/video/", "/photo/", "/infographics/")):
            continue
        if link not in seen:
            seen.add(link)
            out.append(link)
    return out


def parse_vnexpress_article(article_html: str, url: str) -> Article | None:
    title_match = re.search(r'<h1[^>]*class="title-detail"[^>]*>(.*?)</h1>', article_html, re.S)
    if not title_match:
        return None
    title = clean_html_text(title_match.group(1))

    date_match = re.search(r'datetime="([^"]+)"', article_html)
    published = date_match.group(1) if date_match else ""

    desc_match = re.search(r'<p[^>]*class="description"[^>]*>(.*?)</p>', article_html, re.S)
    description = clean_html_text(desc_match.group(1)) if desc_match else ""

    paras = re.findall(r'<p[^>]*class="Normal[^\"]*"[^>]*>(.*?)</p>', article_html, re.S)
    body_paras = [clean_html_text(p) for p in paras]
    body_paras = [p for p in body_paras if p and not (p.startswith("Ảnh:") and len(p) < 120)]
    if description:
        body_paras.insert(0, description)

    body = "\n".join(body_paras).strip()
    if len(body) < 250:
        return None

    return Article(title=title, url=url, published_at=published, body=body)


def crawl(limit: int = 500, workers: int = 12) -> list[Article]:
    links: list[str] = []
    seen: set[str] = set()

    for base in LISTING_URLS:
        page_urls = [base] + [f"{base}-p{i}" for i in range(2, 20)]
        for page_url in page_urls:
            try:
                html_text = fetch_text(page_url)
            except Exception:
                continue
            for link in extract_article_links(html_text):
                if link not in seen:
                    seen.add(link)
                    links.append(link)
            if len(links) >= limit * 3:
                break
        if len(links) >= limit * 3:
            break

    articles: list[Article] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut_to_url = {ex.submit(fetch_text, url): url for url in links}
        for fut in as_completed(fut_to_url):
            url = fut_to_url[fut]
            try:
                article_html = fut.result()
                parsed = parse_vnexpress_article(article_html, url)
            except Exception:
                parsed = None
            if parsed:
                articles.append(parsed)
            if len(articles) >= limit:
                break

    # Keep deterministic order by published_at/title fallback.
    articles.sort(key=lambda a: (a.published_at, a.title), reverse=True)
    if not articles:
        raise RuntimeError('Không crawl được bài nào. Kiểm tra kết nối mạng/proxy và quyền truy cập nguồn tin.')
    return articles[:limit]


def write_csv(path: str, rows: Iterable[Article]) -> None:
    rows = list(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tieu_de", "url", "ngay_gio", "noi_dung_day_du", "nguon"])
        for i, item in enumerate(rows, 1):
            w.writerow([i, item.title, item.url, item.published_at, item.body, item.source])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="du_lieu_the_thao_vi_500_bai.csv")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    rows = crawl(limit=args.limit, workers=args.workers)
    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} records to {args.output}")


if __name__ == "__main__":
    main()
