# Mind Book

## Create a new branch 'mienyeuthuong'
Use CLoudflare Pages to host static website mienyeuthuong.com
```
git branch mienyeuthuong
git switch mienyeuthuong
```

## How to add quotes
Add quotes to quotes.json file 

## How to convert Facebook posts to Blog posts
Chuyển đổi bài viết Facebook thành bài viết Blog tĩnh trên website `mienyeuthuong.com`:

```bash
# Cách 1: Chế độ tương tác từng bước (Interactive)
uv run src/fb_to_blog.py

# Cách 2: Truyền link Facebook trực tiếp
uv run src/fb_to_blog.py --url "https://www.facebook.com/share/p/1F5u3XEdB9/"

# Cách 3: Truyền file nội dung hoặc nhập đầy đủ và tự động push lên GitHub
uv run src/fb_to_blog.py --url "https://www.facebook.com/share/p/1F5u3XEdB9/" --push
```
Sau khi push lên GitHub (nhánh `mienyeuthuong`), Cloudflare Pages sẽ tự động kích hoạt quá trình build và cập nhật website trong vòng 30 giây.
 
