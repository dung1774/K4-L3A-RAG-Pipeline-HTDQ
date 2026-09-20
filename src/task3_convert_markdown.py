"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

from pathlib import Path
from markitdown import MarkItDown
import json

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

MIN_CONTENT_LENGTH = 200

def clean_text(text: str) -> str:
    """Chuẩn hóa nhẹ text nhưng không làm thay đổi nội dung."""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Không để quá nhiều dòng trống liên tiếp
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()


def get_markdown_content(result) -> str:
    """
    Hỗ trợ cả API MarkItDown dùng result.markdown
    và các bản dùng result.text_content.
    """
    markdown = getattr(result, "markdown", None)

    if isinstance(markdown, str) and markdown.strip():
        return markdown

    text_content = getattr(result, "text_content", None)

    if isinstance(text_content, str) and text_content.strip():
        return text_content

    raise ValueError("MarkItDown returned empty content")


def validate_content(content: str, source: str) -> None:
    """Không cho phép sinh Markdown rỗng hoặc quá ngắn."""
    if len(content.strip()) < MIN_CONTENT_LENGTH:
        raise ValueError(
            f"Content too short for {source}: "
            f"{len(content.strip())} characters"
        )


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal sang Markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"

    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        raise FileNotFoundError(f"Missing directory: {legal_dir}")

    converter = MarkItDown()

    supported_extensions = {".pdf", ".docx"}

    files = sorted(
        path
        for path in legal_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in supported_extensions
        and not path.name.startswith(".")
    )

    if not files:
        raise ValueError(f"No PDF/DOCX files found in {legal_dir}")

    success_count = 0

    for path in files:
        try:
            result = converter.convert(str(path))

            content = get_markdown_content(result)
            content = clean_text(content)

            validate_content(content, path.name)

            # Thêm metadata cơ bản ở đầu Markdown.
            header = (
                f"# {path.stem}\n\n"
                f"**Source file:** {path.name}\n\n"
                f"**Document type:** legal\n\n"
                "---\n\n"
            )

            output_path = output_dir / f"{path.stem}.md"

            # Ghi cùng tên mỗi lần chạy -> overwrite,
            # không sinh file duplicate.
            output_path.write_text(
                header + content + "\n",
                encoding="utf-8",
            )

            success_count += 1
            print(
                f"[OK] LEGAL "
                f"{path.name} -> {output_path.name} "
                f"({len(content):,} chars)"
            )

        except Exception as error:
            print(f"[ERROR] LEGAL {path.name}: {error}")

    print(
        f"Legal conversion: "
        f"{success_count}/{len(files)} successful"
    )


def convert_news_articles() -> None:
    """Convert JSON trong landing/news sang Markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"

    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        raise FileNotFoundError(f"Missing directory: {news_dir}")

    files = sorted(
        path
        for path in news_dir.glob("*.json")
        if path.is_file() and not path.name.startswith(".")
    )

    if not files:
        raise ValueError(f"No JSON articles found in {news_dir}")

    required_fields = {
        "url",
        "title",
        "date_crawled",
        "content_markdown",
    }

    success_count = 0

    for path in files:
        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            missing = required_fields - data.keys()

            if missing:
                raise ValueError(
                    f"Missing fields: {sorted(missing)}"
                )

            for field in required_fields:
                if not str(data[field]).strip():
                    raise ValueError(
                        f"Empty field: {field}"
                    )

            title = clean_text(str(data["title"]))
            url = str(data["url"]).strip()
            date_crawled = str(data["date_crawled"]).strip()

            content = clean_text(
                str(data["content_markdown"])
            )

            validate_content(content, path.name)

            header = (
                f"# {title}\n\n"
                f"**Source:** {url}\n\n"
                f"**Crawled:** {date_crawled}\n\n"
                f"**Document type:** news\n\n"
                "---\n\n"
            )

            output_path = output_dir / f"{path.stem}.md"

            output_path.write_text(
                header + content + "\n",
                encoding="utf-8",
            )

            success_count += 1
            print(
                f"[OK] NEWS  "
                f"{path.name} -> {output_path.name} "
                f"({len(content):,} chars)"
            )

        except Exception as error:
            print(f"[ERROR] NEWS {path.name}: {error}")

    print(
        f"News conversion: "
        f"{success_count}/{len(files)} successful"
    )


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== CONVERT LEGAL DOCUMENTS ===")
    convert_legal_docs()

    print("\n=== CONVERT NEWS ARTICLES ===")
    convert_news_articles()

    print(f"\nSaved standardized Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()