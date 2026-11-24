#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook to Blog Post Generator for mienyeuthuong.com
Chuyển đổi bài viết Facebook thành bài viết Blog tĩnh trên Cloudflare Pages & GitHub.
"""

import sys
import os
import re
import json
import html
import unicodedata
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import subprocess

# Đường dẫn thư mục
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SITE_DIR = REPO_ROOT / "mienyeuthuong.com"
POSTS_DIR = SITE_DIR / "posts"
IMAGES_DIR = POSTS_DIR / "images"
POSTS_JSON_FILE = POSTS_DIR / "posts.json"

SITE_DOMAIN = "https://mienyeuthuong.com"
SITE_TITLE = "Miền Yêu Thương"
DEFAULT_AUTHOR = "Anh Tu Dang"
DEFAULT_COVER = "/fbcover-mienyeuthuong.png"


def remove_vietnamese_accents(text: str) -> str:
    """Xóa dấu tiếng Việt phục vụ việc tạo URL slug."""
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[ÌÍỊỈĨ]', 'I', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[ỲÝỴỶỸ]', 'Y', text)
    text = re.sub(r'[đ]', 'd', text)
    text = re.sub(r'[Đ]', 'D', text)
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')


def slugify(text: str) -> str:
    """Tạo slug URL thân thiện từ tiêu đề."""
    text = remove_vietnamese_accents(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    tokens = text.split('-')[:10]
    return '-'.join(tokens) or f"post-{int(datetime.now().timestamp())}"


def format_vietnamese_date(date_obj: datetime) -> str:
    """Định dạng ngày: '24 tháng 11, 2026'."""
    return f"{date_obj.day} tháng {date_obj.month}, {date_obj.year}"


def fetch_facebook_metadata(fb_url: str) -> dict:
    """
    Trích xuất thông tin OpenGraph và preview từ Facebook post URL.
    Sử dụng User-Agent bot để đọc nội dung công khai và canonical URL.
    """
    print(f"[*] Đang kết nối tới Facebook: {fb_url}")
    req = urllib.request.Request(
        fb_url,
        headers={
            "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            final_url = res.geturl()
            content = res.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[!] Không thể cào dữ liệu tự động ({e}).")
        return {
            "canonical_url": fb_url,
            "title": "",
            "description": "",
            "image_url": "",
            "slug": "",
            "author": DEFAULT_AUTHOR
        }

    unquoted_final_url = urllib.parse.unquote(final_url)

    og_title_m = re.findall(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    og_desc_m = re.findall(r'<meta\s+(?:property|name)=["\'](?:og:)?description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    og_img_m = re.findall(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    og_url_m = re.findall(r'<meta\s+property=["\']og:url["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)

    raw_author = html.unescape(og_title_m[0]).strip() if og_title_m else DEFAULT_AUTHOR
    if raw_author.lower() in ("facebook", "log in", "đăng nhập"):
        raw_author = DEFAULT_AUTHOR

    raw_desc = html.unescape(og_desc_m[0]).strip() if og_desc_m else ""
    raw_img = html.unescape(og_img_m[0]).strip() if og_img_m else ""
    raw_canonical = html.unescape(og_url_m[0]).strip() if og_url_m else unquoted_final_url

    slug_hint = ""
    post_slug_m = re.search(r'/posts/([^/]+)/(\d+)', unquoted_final_url)
    if post_slug_m:
        raw_slug_segment = post_slug_m.group(1)
        words = raw_slug_segment.replace('-', ' ').strip()
        slug_hint = words

    post_title = ""
    if raw_desc:
        blocks = raw_desc.strip().split("\n\n")
        first_block = blocks[0].strip()
        first_block_merged = " ".join(l.strip() for l in first_block.splitlines() if l.strip())
        if len(first_block_merged) <= 85:
            post_title = first_block_merged
        else:
            first_line = first_block.splitlines()[0].strip()
            if len(first_line) <= 85:
                post_title = first_line
            else:
                post_title = first_line[:80] + "..."

    if not post_title and slug_hint:
        hint_words = slug_hint.split()[:9]
        post_title = " ".join(hint_words).capitalize()

    if not post_title:
        post_title = "Bài viết mới"

    return {
        "canonical_url": raw_canonical,
        "title": post_title,
        "description": raw_desc,
        "image_url": raw_img,
        "author": raw_author,
        "slug": slugify(post_title)
    }


def save_image_from_url(img_url: str, slug: str) -> str:
    """Tải ảnh bài viết về thư mục cục bộ mienyeuthuong.com/posts/images/."""
    if not img_url:
        return DEFAULT_COVER

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_filename = f"{slug}-cover.jpg"
    out_filepath = IMAGES_DIR / out_filename

    try:
        req = urllib.request.Request(
            img_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.facebook.com/"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            content_type = res.headers.get("Content-Type", "")
            if "image" in content_type:
                data = res.read()
                if len(data) > 1000:
                    with open(out_filepath, "wb") as f:
                        f.write(data)
                    print(f"[*] Đã lưu ảnh cover: images/{out_filename}")
                    return f"images/{out_filename}"
    except Exception:
        pass

    return DEFAULT_COVER


def format_text_to_html(raw_text: str) -> str:
    """
    Chuyển đổi văn bản thô thành HTML có cấu trúc đẹp mắt:
    - Khổ thơ / đoạn văn (<p>)
    - Trích dẫn (<blockquote>)
    - Giữ nguyên nhịp điệu ngắt dòng tự nhiên
    """
    if not raw_text:
        return ""

    paragraphs = raw_text.strip().split("\n\n")
    html_blocks = []

    for p in paragraphs:
        lines = p.strip().split("\n")
        joined_lines = "<br>\n".join(html.escape(l.strip()) for l in lines if l.strip())
        
        if not joined_lines:
            continue

        stripped = p.strip()
        if (stripped.startswith(('"', '“', '”', '«', '>')) and len(stripped) > 5) or stripped.endswith(('"', '”', '»')):
            clean_q = re.sub(r'^[>“"«\s]+|[”"»\s]+$', '', stripped)
            html_blocks.append(f'<blockquote class="post-quote">\n  <p>{html.escape(clean_q)}</p>\n</blockquote>')
        else:
            html_blocks.append(f'<p>{joined_lines}</p>')

    return "\n\n".join(html_blocks)


def calculate_reading_time(text: str) -> str:
    """Ước tính thời gian đọc (phút)."""
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} phút đọc"


def render_post_html(post: dict) -> str:
    """Tạo mã nguồn HTML hoàn chỉnh cho một trang bài viết blog."""
    title_escaped = html.escape(post["title"])
    author_escaped = html.escape(post.get("author", DEFAULT_AUTHOR))
    date_display = post.get("date_display", "")
    reading_time = post.get("reading_time", "1 phút đọc")
    clean_excerpt = " ".join(post.get("excerpt", "").split())
    excerpt_escaped = html.escape(clean_excerpt)
    cover_image = post.get("cover_image", DEFAULT_COVER)
    canonical_url = f"{SITE_DOMAIN}/posts/{post['slug']}.html"
    fb_url = post.get("fb_url", "")
    
    og_image_url = cover_image if cover_image.startswith("http") else f"{SITE_DOMAIN}/{cover_image.lstrip('/')}"
    if cover_image.startswith("images/"):
        og_image_url = f"{SITE_DOMAIN}/posts/{cover_image}"

    tags_html = ""
    if post.get("tags"):
        tag_items = "".join(f'<span class="tag">#{html.escape(t.strip())}</span>' for t in post["tags"] if t.strip())
        tags_html = f'<div class="post-tags">{tag_items}</div>'

    fb_button_html = ""
    if fb_url:
        fb_button_html = f'''
        <div class="fb-source-box">
            <span class="fb-badge">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                Bài viết gốc được chia sẻ trên Facebook
            </span>
            <a href="{html.escape(fb_url)}" target="_blank" rel="noopener noreferrer" class="fb-link">Mở trên Facebook &rarr;</a>
        </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_escaped} | {SITE_TITLE}</title>
  <meta name="description" content="{excerpt_escaped}" />
  <link rel="canonical" href="{canonical_url}" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:title" content="{title_escaped}" />
  <meta property="og:description" content="{excerpt_escaped}" />
  <meta property="og:image" content="{og_image_url}" />
  <meta property="article:published_time" content="{post.get('date', '')}" />
  <meta property="article:author" content="{author_escaped}" />

  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image" />
  <meta property="twitter:url" content="{canonical_url}" />
  <meta property="twitter:title" content="{title_escaped}" />
  <meta property="twitter:description" content="{excerpt_escaped}" />
  <meta property="twitter:image" content="{og_image_url}" />

  <!-- Schema.org JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": {json.dumps(post["title"], ensure_ascii=False)},
    "description": {json.dumps(clean_excerpt, ensure_ascii=False)},
    "image": "{og_image_url}",
    "datePublished": "{post.get('date', '')}",
    "author": {{
      "@type": "Person",
      "name": {json.dumps(author_escaped, ensure_ascii=False)}
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "{SITE_TITLE}",
      "url": "{SITE_DOMAIN}"
    }},
    "mainEntityOfPage": {{
      "@type": "WebPage",
      "@id": "{canonical_url}"
    }}
  }}
  </script>

  <style>
    :root {{
      --bg-color: #001f3f;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #f39c12;
      --accent-hover: #e67e22;
      --link: #38bdf8;
      --font-body: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-serif: Georgia, Cambria, "Times New Roman", Times, serif;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-color);
      color: var(--text-main);
      font-family: var(--font-body);
      line-height: 1.85;
      font-size: 1.15rem;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* Top navigation bar */
    .top-nav {{
      border-bottom: 1px solid var(--card-border);
      padding: 1.1rem 1.5rem;
      background: rgba(0, 31, 63, 0.85);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 100;
    }}

    .nav-container {{
      max-width: 800px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .nav-brand {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #fff;
      text-decoration: none;
      font-weight: 700;
      font-size: 1.15rem;
      letter-spacing: 0.5px;
    }}

    .nav-brand:hover {{
      color: var(--accent);
    }}

    .nav-links {{
      display: flex;
      gap: 1.25rem;
    }}

    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.95rem;
      transition: color 0.2s;
    }}

    .nav-link:hover {{
      color: var(--accent);
    }}

    /* Main article wrapper */
    .article-container {{
      max-width: 740px;
      margin: 2.5rem auto 4rem;
      padding: 0 1.25rem;
      width: 100%;
      flex: 1;
    }}

    .back-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      color: var(--link);
      text-decoration: none;
      font-size: 0.95rem;
      margin-bottom: 2rem;
      transition: transform 0.2s;
    }}

    .back-btn:hover {{
      transform: translateX(-4px);
    }}

    .article-header {{
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
    }}

    .article-title {{
      font-size: 2.25rem;
      font-weight: 800;
      line-height: 1.35;
      margin-bottom: 1rem;
      color: #ffffff;
      letter-spacing: -0.3px;
    }}

    .article-meta {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.85rem;
      color: var(--text-muted);
      font-size: 0.95rem;
    }}

    .meta-separator {{
      opacity: 0.4;
    }}

    .cover-image-box {{
      margin: 2rem 0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      background: #001428;
    }}

    .cover-image {{
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
      max-height: 480px;
    }}

    /* Article content styling */
    .article-body {{
      font-size: 1.15rem;
      line-height: 1.9;
      color: #e2e8f0;
    }}

    .article-body p {{
      margin-bottom: 1.5rem;
    }}

    .post-quote {{
      margin: 2rem 0;
      padding: 1.25rem 1.75rem;
      border-left: 4px solid var(--accent);
      background: rgba(243, 156, 18, 0.1);
      border-radius: 0 8px 8px 0;
      font-family: var(--font-serif);
      font-style: italic;
      color: #fef3c7;
      font-size: 1.2rem;
    }}

    .post-quote p {{
      margin: 0;
    }}

    .post-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 2.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--card-border);
    }}

    .tag {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 0.3rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
    }}

    /* Facebook link box */
    .fb-source-box {{
      margin: 2.5rem 0;
      padding: 1.1rem 1.35rem;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .fb-badge {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.95rem;
      color: #bae6fd;
      font-weight: 500;
    }}

    .fb-link {{
      color: #38bdf8;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.95rem;
      transition: color 0.2s;
    }}

    .fb-link:hover {{
      color: #7dd3fc;
      text-decoration: underline;
    }}

    /* Footer */
    footer {{
      border-top: 1px solid var(--card-border);
      padding: 2.5rem 1.25rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.9rem;
      background: rgba(0, 0, 0, 0.25);
    }}

    footer a {{
      color: var(--link);
      text-decoration: none;
    }}

    @media (max-width: 640px) {{
      .article-title {{
        font-size: 1.8rem;
      }}
      body {{
        font-size: 1.05rem;
      }}
      .article-container {{
        margin-top: 1.5rem;
      }}
    }}
  </style>
</head>
<body>

  <nav class="top-nav">
    <div class="nav-container">
      <a href="/" class="nav-brand">✨ {SITE_TITLE}</a>
      <div class="nav-links">
        <a href="/" class="nav-link">Trâm ngôn</a>
        <a href="/posts/" class="nav-link" style="color: var(--accent);">Góc bài viết</a>
      </div>
    </div>
  </nav>

  <main class="article-container">
    <a href="/posts/" class="back-btn">&larr; Quay lại danh sách bài viết</a>

    <header class="article-header">
      <h1 class="article-title">{title_escaped}</h1>
      <div class="article-meta">
        <span>✍️ {author_escaped}</span>
        <span class="meta-separator">&bull;</span>
        <span>📅 {date_display}</span>
        <span class="meta-separator">&bull;</span>
        <span>⏱️ {reading_time}</span>
      </div>
    </header>

    {'<div class="cover-image-box"><img src="' + cover_image + '" alt="' + title_escaped + '" class="cover-image" /></div>' if cover_image and cover_image != DEFAULT_COVER else ''}

    <article class="article-body">
      {post['content_html']}
    </article>

    {tags_html}

    {fb_button_html}
  </main>

  <footer>
    <p>&copy; {datetime.now().year} <a href="/">{SITE_TITLE}</a> &bull; Lưu giữ những khoảnh khắc và bài học yêu thương.</p>
  </footer>

</body>
</html>
'''
    return html_content


def render_index_html(posts: list) -> str:
    """Tạo trang chủ danh sách bài viết (posts/index.html)."""
    cards_html = []
    sorted_posts = sorted(posts, key=lambda x: x.get("date", ""), reverse=True)

    for p in sorted_posts:
        title = html.escape(p["title"])
        excerpt = html.escape(" ".join(p.get("excerpt", "").split()))
        slug = p["slug"]
        date_display = p.get("date_display", "")
        reading_time = p.get("reading_time", "1 phút đọc")
        cover_image = p.get("cover_image", DEFAULT_COVER)
        
        tags_badges = ""
        if p.get("tags"):
            tags_badges = "".join(f'<span class="card-tag">#{html.escape(t.strip())}</span>' for t in p["tags"][:3])

        card = f'''
        <article class="post-card">
          <div class="card-cover-box">
            <img src="{cover_image}" alt="{title}" class="card-cover" loading="lazy" />
          </div>
          <div class="card-content">
            <div class="card-meta">
              <span>📅 {date_display}</span>
              <span>&bull;</span>
              <span>{reading_time}</span>
            </div>
            <h2 class="card-title">
              <a href="{slug}.html">{title}</a>
            </h2>
            <p class="card-excerpt">{excerpt}</p>
            <div class="card-footer">
              <div class="card-tags">{tags_badges}</div>
              <a href="{slug}.html" class="read-more">Đọc tiếp &rarr;</a>
            </div>
          </div>
        </article>
        '''
        cards_html.append(card)

    cards_joined = "\n".join(cards_html) if cards_html else '<p style="text-align: center; color: var(--text-muted); padding: 3rem 0;">Chưa có bài viết nào.</p>'

    html_content = f'''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Góc Bài Viết | {SITE_TITLE}</title>
  <meta name="description" content="Những bài viết, câu chuyện và chiêm nghiệm về cuộc sống và tình yêu thương." />
  <link rel="canonical" href="{SITE_DOMAIN}/posts/" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />

  <meta property="og:type" content="website" />
  <meta property="og:url" content="{SITE_DOMAIN}/posts/" />
  <meta property="og:title" content="Góc Bài Viết | {SITE_TITLE}" />
  <meta property="og:description" content="Những bài viết, câu chuyện và chiêm nghiệm về cuộc sống và tình yêu thương." />
  <meta property="og:image" content="{SITE_DOMAIN}{DEFAULT_COVER}" />

  <style>
    :root {{
      --bg-color: #001f3f;
      --card-bg: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #f39c12;
      --accent-hover: #e67e22;
      --link: #38bdf8;
      --font-body: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-color);
      color: var(--text-main);
      font-family: var(--font-body);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    .top-nav {{
      border-bottom: 1px solid var(--card-border);
      padding: 1.1rem 1.5rem;
      background: rgba(0, 31, 63, 0.85);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 100;
    }}

    .nav-container {{
      max-width: 960px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .nav-brand {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #fff;
      text-decoration: none;
      font-weight: 700;
      font-size: 1.15rem;
    }}

    .nav-brand:hover {{
      color: var(--accent);
    }}

    .nav-links {{
      display: flex;
      gap: 1.25rem;
    }}

    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.95rem;
    }}

    .nav-link:hover {{
      color: var(--accent);
    }}

    .hero-header {{
      text-align: center;
      padding: 3.5rem 1rem 2rem;
      max-width: 720px;
      margin: 0 auto;
    }}

    .hero-title {{
      font-size: 2.6rem;
      font-weight: 800;
      margin-bottom: 0.75rem;
      color: #ffffff;
      letter-spacing: -0.5px;
    }}

    .hero-desc {{
      color: var(--text-muted);
      font-size: 1.15rem;
    }}

    .posts-container {{
      max-width: 960px;
      margin: 1.5rem auto 4rem;
      padding: 0 1.25rem;
      width: 100%;
      flex: 1;
    }}

    .posts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
      gap: 1.85rem;
    }}

    .post-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s;
    }}

    .post-card:hover {{
      transform: translateY(-5px);
      border-color: rgba(243, 156, 18, 0.4);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
    }}

    .card-cover-box {{
      height: 190px;
      overflow: hidden;
      background: #001428;
    }}

    .card-cover {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }}

    .post-card:hover .card-cover {{
      transform: scale(1.05);
    }}

    .card-content {{
      padding: 1.35rem;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}

    .card-meta {{
      font-size: 0.85rem;
      color: var(--text-muted);
      display: flex;
      gap: 0.5rem;
      align-items: center;
      margin-bottom: 0.6rem;
    }}

    .card-title {{
      font-size: 1.3rem;
      font-weight: 700;
      margin-bottom: 0.65rem;
      line-height: 1.4;
    }}

    .card-title a {{
      color: #fff;
      text-decoration: none;
      transition: color 0.2s;
    }}

    .card-title a:hover {{
      color: var(--accent);
    }}

    .card-excerpt {{
      color: #94a3b8;
      font-size: 0.95rem;
      line-height: 1.6;
      margin-bottom: 1.25rem;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      flex: 1;
    }}

    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.85rem;
      border-top: 1px solid var(--card-border);
      font-size: 0.85rem;
    }}

    .card-tags {{
      display: flex;
      gap: 0.35rem;
      flex-wrap: wrap;
    }}

    .card-tag {{
      color: var(--text-muted);
    }}

    .read-more {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}

    .read-more:hover {{
      color: var(--accent-hover);
      text-decoration: underline;
    }}

    footer {{
      border-top: 1px solid var(--card-border);
      padding: 2.5rem 1.25rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.9rem;
      background: rgba(0, 0, 0, 0.25);
    }}

    footer a {{
      color: var(--link);
      text-decoration: none;
    }}

    @media (max-width: 640px) {{
      .hero-title {{
        font-size: 2.1rem;
      }}
      .posts-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>

  <nav class="top-nav">
    <div class="nav-container">
      <a href="/" class="nav-brand">✨ {SITE_TITLE}</a>
      <div class="nav-links">
        <a href="/" class="nav-link">Trâm ngôn</a>
        <a href="/posts/" class="nav-link" style="color: var(--accent);">Góc bài viết</a>
      </div>
    </div>
  </nav>

  <header class="hero-header">
    <h1 class="hero-title">Góc Bài Viết</h1>
    <p class="hero-desc">Lắng đọng cùng những câu chuyện, bài học và chiêm nghiệm về cuộc sống và tình yêu thương.</p>
  </header>

  <main class="posts-container">
    <div class="posts-grid">
      {cards_joined}
    </div>
  </main>

  <footer>
    <p>&copy; {datetime.now().year} <a href="/">{SITE_TITLE}</a> &bull; Lưu giữ những khoảnh khắc và bài học yêu thương.</p>
  </footer>

</body>
</html>
'''
    return html_content


def generate_rss_and_sitemap(posts: list):
    """Tạo sitemap.xml và feed.xml phục vụ SEO và đọc tin RSS."""
    # 1. Sitemap.xml
    sitemap_items = [
        f'  <url><loc>{SITE_DOMAIN}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{SITE_DOMAIN}/posts/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>'
    ]
    for p in posts:
        slug = p["slug"]
        date = p.get("date", datetime.now().strftime("%Y-%m-%d"))
        sitemap_items.append(
            f'  <url><loc>{SITE_DOMAIN}/posts/{slug}.html</loc><lastmod>{date}</lastmod><priority>0.8</priority></url>'
        )

    sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_items)}
</urlset>'''

    with open(SITE_DIR / "sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    # 2. RSS feed.xml
    rss_items = []
    for p in posts:
        p_title = html.escape(p["title"])
        p_link = f"{SITE_DOMAIN}/posts/{p['slug']}.html"
        p_desc = html.escape(" ".join(p.get("excerpt", "").split()))
        p_date = p.get("date", datetime.now().strftime("%Y-%m-%d"))
        rss_items.append(f'''    <item>
      <title>{p_title}</title>
      <link>{p_link}</link>
      <guid>{p_link}</guid>
      <pubDate>{p_date}</pubDate>
      <description>{p_desc}</description>
    </item>''')

    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_TITLE} - Góc Bài Viết</title>
    <link>{SITE_DOMAIN}/posts/</link>
    <description>Những bài viết, câu chuyện và chiêm nghiệm về cuộc sống và tình yêu thương.</description>
    <language>vi</language>
{chr(10).join(rss_items)}
  </channel>
</rss>'''

    with open(SITE_DIR / "feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("[*] Đã cập nhật sitemap.xml & feed.xml (RSS)")


def update_homepage_navigation():
    """Tạo nút dẫn đến 'Góc bài viết' tại trang chủ index.html."""
    index_file = SITE_DIR / "index.html"
    if not index_file.exists():
        return

    content = index_file.read_text(encoding="utf-8")
    if '/posts/' in content:
        return

    nav_style = """
    .top-blog-btn {
      position: absolute;
      top: 1.25rem;
      right: 1.5rem;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.25);
      color: #ffffff;
      padding: 0.45rem 1rem;
      border-radius: 9999px;
      text-decoration: none;
      font-size: 0.95rem;
      font-weight: 500;
      backdrop-filter: blur(8px);
      transition: all 0.25s ease;
      z-index: 999;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .top-blog-btn:hover {
      background: rgba(243, 156, 18, 0.25);
      border-color: #f39c12;
      color: #fcd34d;
      transform: translateY(-2px);
    }
    """

    blog_btn_html = '<a href="/posts/" class="top-blog-btn">📖 Góc bài viết &rarr;</a>\n'

    if '</style>' in content:
        content = content.replace('</style>', f"{nav_style}\n  </style>", 1)
    if '<body>' in content:
        content = content.replace('<body>', f"<body>\n  {blog_btn_html}", 1)

    index_file.write_text(content, encoding="utf-8")
    print("[*] Đã thêm nút 'Góc bài viết' trên trang chủ mienyeuthuong.com/index.html")


def load_posts() -> list:
    """Đọc dữ liệu posts.json."""
    if POSTS_JSON_FILE.exists():
        try:
            with open(POSTS_JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Lỗi đọc posts.json: {e}")
    return []


def save_posts(posts: list):
    """Lưu dữ liệu posts.json."""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(POSTS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def rebuild_all_site():
    """Tạo lại toàn bộ các file HTML từ cơ sở dữ liệu posts.json."""
    posts = load_posts()
    print(f"[*] Đang tái tạo lại toàn bộ blog ({len(posts)} bài viết)...")
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    
    for p in posts:
        post_html = render_post_html(p)
        post_file = POSTS_DIR / f"{p['slug']}.html"
        post_file.write_text(post_html, encoding="utf-8")
    
    index_html = render_index_html(posts)
    (POSTS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    
    generate_rss_and_sitemap(posts)
    update_homepage_navigation()
    print("[+] Hoàn tất tái tạo blog!")


def add_or_update_post(
    fb_url: str,
    title: str = "",
    content_text: str = "",
    author: str = "",
    tags: list = None,
    custom_slug: str = "",
    image_url: str = ""
) -> dict:
    """Tạo bài viết mới hoặc cập nhật bài viết cũ."""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    meta = {}
    if fb_url:
        meta = fetch_facebook_metadata(fb_url)

    final_title = title.strip() or meta.get("title") or "Bài viết mới"
    final_author = author.strip() or meta.get("author") or DEFAULT_AUTHOR
    final_slug = custom_slug.strip() or meta.get("slug") or slugify(final_title)
    final_tags = tags if tags is not None else ["Yêu thương", "Cuộc sống"]

    if not content_text:
        content_text = meta.get("description", "")
        if not content_text:
            content_text = final_title

    paragraphs = [p.strip() for p in content_text.split("\n\n") if p.strip()]
    first_para = paragraphs[0] if paragraphs else final_title
    excerpt = " ".join(first_para.split())[:180] + ("..." if len(first_para) > 180 else "")

    chosen_img_url = image_url or meta.get("image_url", "")
    cover_image_path = save_image_from_url(chosen_img_url, final_slug)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    date_display = format_vietnamese_date(now)

    content_html = format_text_to_html(content_text)
    reading_time = calculate_reading_time(content_text)

    post_entry = {
        "title": final_title,
        "slug": final_slug,
        "author": final_author,
        "date": date_str,
        "date_display": date_display,
        "excerpt": excerpt,
        "cover_image": cover_image_path,
        "content_html": content_html,
        "raw_content": content_text,
        "reading_time": reading_time,
        "tags": final_tags,
        "fb_url": fb_url
    }

    posts = load_posts()
    existing_idx = next((i for i, p in enumerate(posts) if p["slug"] == final_slug), None)

    if existing_idx is not None:
        print(f"[*] Cập nhật bài viết hiện có: {final_slug}")
        post_entry["date"] = posts[existing_idx].get("date", date_str)
        post_entry["date_display"] = posts[existing_idx].get("date_display", date_display)
        posts[existing_idx] = post_entry
    else:
        print(f"[*] Thêm bài viết mới: {final_slug}")
        posts = [p for p in posts if p["slug"] != "anh-tu-dang"]
        posts.insert(0, post_entry)

    save_posts(posts)

    post_file = POSTS_DIR / f"{final_slug}.html"
    post_html = render_post_html(post_entry)
    post_file.write_text(post_html, encoding="utf-8")
    print(f"[+] Đã tạo file HTML: mienyeuthuong.com/posts/{post_file.name}")

    index_html = render_index_html(posts)
    (POSTS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("[+] Đã cập nhật: mienyeuthuong.com/posts/index.html")

    generate_rss_and_sitemap(posts)
    update_homepage_navigation()

    live_url = f"{SITE_DOMAIN}/posts/{final_slug}.html"
    print(f"\n🎉 Thành công! Đường dẫn bài viết sẽ là: {live_url}")
    return post_entry


def git_commit_and_push(commit_msg: str, branch: str = "mienyeuthuong"):
    """Thực hiện git commit và push lên GitHub để kích hoạt Cloudflare Pages deploy."""
    print(f"\n[*] Đang chuẩn bị đồng bộ lên GitHub (nhánh: {branch})...")
    try:
        res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=REPO_ROOT)
        current_branch = res.stdout.strip()
        print(f"[*] Nhánh hiện tại: {current_branch}")

        subprocess.run(["git", "add", "mienyeuthuong.com"], cwd=REPO_ROOT, check=True)
        
        commit_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, capture_output=True, text=True)
        if "nothing to commit" in commit_res.stdout:
            print("[*] Không có thay đổi mới cần commit.")
        else:
            print(f"[+] Đã commit: {commit_msg}")

        target_branch = branch if branch else current_branch
        print(f"[*] Đang push lên origin {target_branch}...")
        push_res = subprocess.run(["git", "push", "origin", f"HEAD:{target_branch}"], cwd=REPO_ROOT, capture_output=True, text=True)
        if push_res.returncode == 0:
            print("[+] Push thành công lên GitHub! Cloudflare Pages sẽ tự động deploy trong 30 giây.")
        else:
            print(f"[!] Phản hồi từ git push: {push_res.stderr or push_res.stdout}")
    except Exception as e:
        print(f"[!] Lỗi git commit/push: {e}")


def interactive_mode():
    """Giao diện dòng lệnh tương tác từng bước dễ dùng cho người dùng."""
    print("\n" + "=" * 65)
    print("  CÔNG CỤ CHUYỂN FACEBOOK POST SANG BLOG CHO MIENYEUTHUONG.COM")
    print("=" * 65)

    url_input = input("\n1. Nhập link Facebook (hoặc Enter để nhập bài viết trực tiếp): ").strip()
    
    meta = {}
    if url_input:
        meta = fetch_facebook_metadata(url_input)
        print(f"   -> Tiêu đề trích xuất: {meta.get('title')}")
        print(f"   -> Tác giả: {meta.get('author')}")
        if meta.get("description"):
            preview_short = meta['description'].replace('\n', ' ')[:100]
            print(f"   -> Nội dung xem trước: {preview_short}...")

    default_title = meta.get('title', 'Bài viết mới')
    title_input = input(f"\n2. Nhập Tiêu đề bài viết [Mặc định: {default_title}]: ").strip()
    title = title_input or default_title

    print("\n3. Nội dung bài viết:")
    print("   [A] Dùng nội dung vừa trích xuất từ Facebook")
    print("   [B] Nhập/Dán nội dung đầy đủ trực tiếp (paste text)")
    print("   [C] Nhập từ file text/markdown (.txt, .md)")
    choice = input("   Lựa chọn của bạn (A/B/C) [Mặc định: A]: ").strip().upper() or "A"

    content = ""
    if choice == "B":
        print("\n   Dán nội dung bài viết dưới đây (nhấn Enter rồi gõ EOF trên một dòng riêng để kết thúc):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            except EOFError:
                break
        content = "\n".join(lines).strip()
    elif choice == "C":
        fpath = input("   Nhập đường dẫn file: ").strip()
        if os.path.exists(fpath):
            content = Path(fpath).read_text(encoding="utf-8").strip()
        else:
            print(f"   [!] Không tìm thấy file {fpath}, dùng nội dung trích xuất từ Facebook.")
            content = meta.get("description", "")
    else:
        content = meta.get("description", "")

    author_default = meta.get('author', DEFAULT_AUTHOR)
    author_input = input(f"\n4. Tác giả [Mặc định: {author_default}]: ").strip()
    author = author_input or author_default

    tags_input = input("\n5. Thẻ/Tags (ngăn cách bởi dấu phẩy) [Mặc định: Yêu thương, Cuộc sống]: ").strip()
    tags = [t.strip() for t in tags_input.split(",")] if tags_input else ["Yêu thương", "Cuộc sống"]

    post = add_or_update_post(
        fb_url=url_input,
        title=title,
        content_text=content,
        author=author,
        tags=tags
    )

    push_choice = input("\n6. Bạn có muốn tự động Commit & Push lên GitHub để Cloudflare Pages xuất bản ngay không? (y/N): ").strip().lower()
    if push_choice in ("y", "yes"):
        git_commit_and_push(f"blog: thêm bài viết '{post['title']}'", branch="mienyeuthuong")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Chuyển Facebook Post thành Blog Post cho mienyeuthuong.com")
    parser.add_argument("--url", help="URL bài viết Facebook")
    parser.add_argument("--title", help="Tiêu đề bài viết (tuỳ chọn)")
    parser.add_argument("--content", help="Nội dung bài viết dạng văn bản")
    parser.add_argument("--file", help="Đường dẫn file .txt/.md chứa nội dung bài viết")
    parser.add_argument("--author", help="Tên tác giả (mặc định: Anh Tu Dang)")
    parser.add_argument("--tags", help="Danh sách thẻ, ngăn cách bởi dấu phẩy")
    parser.add_argument("--slug", help="Slug tùy chỉnh cho bài viết")
    parser.add_argument("--push", action="store_true", help="Tự động commit và push lên GitHub sau khi tạo")
    parser.add_argument("--branch", default="mienyeuthuong", help="Nhánh GitHub cần push (mặc định: mienyeuthuong)")
    parser.add_argument("--rebuild", action="store_true", help="Tái tạo lại toàn bộ blog từ posts.json")

    args = parser.parse_args()

    if args.rebuild:
        rebuild_all_site()
        if args.push:
            git_commit_and_push("blog: tái tạo lại toàn bộ blog", branch=args.branch)
        return

    if not args.url and not args.content and not args.file:
        interactive_mode()
        return

    content_text = args.content or ""
    if args.file and os.path.exists(args.file):
        content_text = Path(args.file).read_text(encoding="utf-8")

    tags_list = [t.strip() for t in args.tags.split(",")] if args.tags else None

    post = add_or_update_post(
        fb_url=args.url or "",
        title=args.title or "",
        content_text=content_text,
        author=args.author or "",
        tags=tags_list,
        custom_slug=args.slug or ""
    )

    if args.push:
        git_commit_and_push(f"blog: thêm bài viết '{post['title']}'", branch=args.branch)


if __name__ == "__main__":
    main()
