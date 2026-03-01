# DAT301m
## Crawl dữ liệu thể thao tiếng Việt (full article)

Script `scripts/crawl_sports_articles.py` dùng để crawl bài thể thao tiếng Việt từ VnExpress và xuất CSV chứa **nội dung đầy đủ** (không chỉ tóm tắt).

Ví dụ:

```bash
python scripts/crawl_sports_articles.py --output du_lieu_the_thao_vi_500_bai.csv --limit 500
```

CSV output gồm các cột:
- `id`
- `tieu_de`
- `url`
- `ngay_gio`
- `noi_dung_day_du`
- `nguon`
