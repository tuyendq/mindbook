Khách hàng của tôi thường post nội dung trên facebook kiểu như ở link https://www.facebook.com/share/p/1F5u3XEdB9/
Khách hàng muốn chuyển những facebook post như thế thanh các blog   post ở website đang có sẵn httpss://mienyeuthuong.com. 
Website htttps://mienyeuthuong.com hiện đang host ở dịch vụ Pages miễn phí của Cloudfllare. Nội dung gốc của  website được lưu ở một repo của github
Giúp tôi viết python code để thực hiện yêu cầu này

Ran check python path from user
Ran check uv command
Ran check git log on mienyeuthuong branch
Ran list installed python packages
Checked task List installed python packages
Ran test extracting OpenGraph data from Facebook · Exited with code 1
Created test_fb.py
Ran run test_fb.py
Created inspect_meta.py
Ran inspect meta tags
Created check_scripts.py
Ran check scripts in HTML response
Created find_occurrences.py
Ran find occurrences in unescaped content
Created test_img.py
Ran test image download
Created test_img2.py
Ran test image download with Chrome UA
Ran check git status
Ran compare mindbookdev and mienyeuthuong branches
Ran create posts/images directory
Created fb_to_blog.py
Ran run fb_to_blog.py with sample Facebook URL
Analyzed posts.json:L1-19
Analyzed anh-tu-dang.html:L1-70
Created test_regex.py
Ran test multi-line regex
Created test_lookaside.py
Ran test lookaside image download
Writing fb_to_blog.py
Edited fb_to_blog.py
Ran run updated fb_to_blog.py
Analyzed posts.json:L1-19
Analyzed dieu-chua-tinh-luon-tron-ven-hon-dieu-ta-tinh.html:L1-100
Analyzed index.html:L200-300
Analyzed index.html:L1-60
Analyzed index.html:L60-122
Ran check git status in mindbook repo
Edited fb_to_blog.py
Ran rebuild blog site
Ran list all files in mienyeuthuong.com
Ran remove temporary html test file
Ran check git status
Analyzed README.md:L1-11
Edited README.md
Ran check git status

Tôi đã xây dựng hoàn chỉnh mã nguồn Python `src/fb_to_blog.py` tích hợp trực tiếp vào dự án `mindbook` để chuyển đổi các bài viết Facebook thành bài viết Blog tĩnh trên website [mienyeuthuong.com](https://mienyeuthuong.com).

---

### 1. Luồng hoạt động tổng thể (Workflow)

```
[ Link bài viết Facebook ]
            │
            ▼
┌──────────────────────────────────────────────┐
│  src/fb_to_blog.py                           │
│  - Bóc tách tiêu đề, tác giả, ảnh, nội dung   │
│  - Chuẩn hóa Slug tiếng Việt thân thiện SEO  │
│  - Tạo file HTML bài viết: posts/<slug>.html │
│  - Cập nhật trang danh sách: posts/index.html│
│  - Cập nhật sitemap.xml & feed.xml (RSS)     │
│  - Lưu trữ cơ sở dữ liệu bài viết posts.json │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Git Commit & Push lên GitHub                │
│  (Nhánh: mienyeuthuong)                      │
└──────────────────────┬───────────────────────┘
                       │ (Tự động kích hoạt)
                       ▼
┌──────────────────────────────────────────────┐
│  Cloudflare Pages Build & Deploy             │
│  Website cập nhật bài mới sau ~30 giây        │
└──────────────────────────────────────────────┘
```

---

### 2. Các thành phần đã được tạo trong dự án

1. **Bộ sinh Blog Python**: [src/fb_to_blog.py](file:///c:/projects/mindbook/src/fb_to_blog.py)
   * Sử dụng hoàn toàn thư viện chuẩn của Python (`urllib`, `re`, `html`, `json`, `datetime`, `pathlib`, `subprocess`), không yêu cầu cài thêm package bên ngoài phức tạp.
   * Chế độ **Interactive** (hướng dẫn từng bước) và chế độ **CLI** (dòng lệnh 1 chạm).
   * Tự động tải ảnh bìa về lưu tại thư mục [posts/images/](file:///c:/projects/mindbook/mienyeuthuong.com/posts/images) để tránh trường hợp link ảnh CDN của Facebook bị hết hạn token.
2. **Trang bài viết mẫu đã xuất bản**: [dieu-chua-tinh-luon-tron-ven-hon-dieu-ta-tinh.html](file:///c:/projects/mindbook/mienyeuthuong.com/posts/dieu-chua-tinh-luon-tron-ven-hon-dieu-ta-tinh.html)
   * Giao diện chuẩn màu xanh thẫm thanh tịnh (`#001f3f`) đồng bộ với Miền Yêu Thương.
   * Thẻ OpenGraph (Facebook/Zalo Share Card), Twitter Card và Schema `BlogPosting` chuẩn SEO Google.
   * Hộp nguồn dẫn về Facebook gốc: *"Mở trên Facebook →"*.
3. **Trang danh sách bài viết**: [posts/index.html](file:///c:/projects/mindbook/mienyeuthuong.com/posts/index.html)
   * Hiển thị danh sách bài viết dạng thẻ bài (Card) kèm thời gian đọc, ngày đăng, ảnh bìa và nhãn thẻ (`#Tags`).
4. **Liên kết trên trang chủ**: [mienyeuthuong.com/index.html](file:///c:/projects/mindbook/mienyeuthuong.com/index.html)
   * Bổ sung nút bấm tinh tế `📖 Góc bài viết →` ở góc trên cùng bên phải, không làm xáo trộn khung trâm ngôn hiện có.
5. **SEO & RSS**:
   * Tự động sinh [sitemap.xml](file:///c:/projects/mindbook/mienyeuthuong.com/sitemap.xml) và [feed.xml](file:///c:/projects/mindbook/mienyeuthuong.com/feed.xml) (RSS 2.0).

---

### 3. Hướng dẫn sử dụng

Bạn có thể chạy script bằng công cụ `uv` đã cài sẵn trên máy:

#### Cách 1: Chế độ hướng dẫn tương tác (Khuyên dùng)
Gõ lệnh và làm theo lời nhắc trên màn hình:
```powershell
uv run src/fb_to_blog.py
```
*Script sẽ hỏi:*
1. Dán link bài viết Facebook (ví dụ: `https://www.facebook.com/share/p/1F5u3XEdB9/`).
2. Xác nhận hoặc sửa lại Tiêu đề bài viết.
3. Chọn nguồn nội dung: Lấy từ Facebook preview, dán nội dung đầy đủ trực tiếp, hoặc đọc từ file `.txt`.
4. Nhập Tác giả và Thẻ bài viết.
5. Xác nhận tự động Commit & Push lên GitHub để xuất bản ngay.

#### Cách 2: Chạy trực tiếp một dòng lệnh (CLI)
```powershell
# Chuyển đổi từ link và tự động push lên GitHub
uv run src/fb_to_blog.py --url "https://www.facebook.com/share/p/1F5u3XEdB9/" --push

# Tạo bài viết với nội dung đầy đủ từ một file văn bản
uv run src/fb_to_blog.py --url "https://www.facebook.com/share/p/1F5u3XEdB9/" --file "bai-viet.txt" --push
```

#### Cách 3: Tái tạo lại toàn bộ blog
Nếu bạn chỉnh sửa file dữ liệu [posts.json](file:///c:/projects/mindbook/mienyeuthuong.com/posts/posts.json), chỉ cần chạy:
```powershell
uv run src/fb_to_blog.py --rebuild --push
```

---

### 4. Đẩy các thay đổi hiện tại lên GitHub

Các file blog và bài viết đầu tiên đã được tạo sẵn trong thư mục `mienyeuthuong.com/`. Để đưa lên Cloudflare Pages ngay bây giờ, bạn chỉ cần thực hiện lệnh Git:

```powershell
git checkout mienyeuthuong
git merge mindbookdev
git push origin mienyeuthuong
```
Sau khi push thành công, Cloudflare Pages sẽ tự động kích hoạt tiến trình triển khai và bài viết sẽ xuất hiện trực tiếp tại:
👉 `https://mienyeuthuong.com/posts/dieu-chua-tinh-luon-tron-ven-hon-dieu-ta-tinh.html`

---

### 5. Lưu ý kỹ thuật về bài viết Facebook

* **Bài viết trang cá nhân (Personal Profile)**: Facebook thường chỉ trả về phần xem trước (~200–300 ký tự) cho các crawler công khai. Do đó, chế độ `Interactive` cho phép bạn dán bổ sung phần thân bài viết đầy đủ nếu bài viết gốc quá dài.
* **Bài viết Fanpage (Trang kinh doanh / Cộng đồng)**: Nếu sau này khách hàng đăng bài qua Fanpage, bạn có thể tích hợp thêm Meta Graph API token để hệ thống tự động kéo 100% nội dung bài và tất cả album ảnh mà không cần thao tác thủ công.