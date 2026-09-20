"""
Task 1 — Thu thập tài liệu chính sách/quy định về du lịch Việt Nam.

Nhóm thu thập thủ công các tài liệu pháp lý từ nguồn công khai
và lưu file gốc vào data/landing/legal/.

Task này chịu trách nhiệm:
    1. Tạo thư mục landing/legal nếu chưa tồn tại.
    2. Kiểm tra có tối thiểu 3 tài liệu hợp lệ.
    3. Chỉ chấp nhận PDF/DOC/DOCX.
    4. Kiểm tra file không rỗng/quá nhỏ.
"""

from pathlib import Path


DATA_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "landing"
    / "legal"
)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

MIN_DOCUMENTS = 3
MIN_FILE_SIZE = 1024  # 1 KB


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Ready: {DATA_DIR}")


def get_legal_documents() -> list[Path]:
    """Lấy danh sách tài liệu legal hợp lệ trong landing/legal."""

    if not DATA_DIR.exists():
        return []

    return sorted(
        path
        for path in DATA_DIR.iterdir()
        if (
            path.is_file()
            and not path.name.startswith(".")
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )


def validate_documents(
    documents: list[Path],
) -> None:
    """Kiểm tra số lượng và kích thước tài liệu."""

    if len(documents) < MIN_DOCUMENTS:
        raise ValueError(
            f"Need at least {MIN_DOCUMENTS} legal documents, "
            f"found {len(documents)} in {DATA_DIR}"
        )

    invalid_files = [
        path
        for path in documents
        if path.stat().st_size <= MIN_FILE_SIZE
    ]

    if invalid_files:
        names = ", ".join(
            path.name
            for path in invalid_files
        )

        raise ValueError(
            "Legal documents must be larger than "
            f"{MIN_FILE_SIZE} bytes: {names}"
        )


def download_documents() -> None:
    """
    Xác nhận các tài liệu đã được tải thủ công.

    Tài liệu được tải từ nguồn công khai bằng trình duyệt
    và lưu trực tiếp vào data/landing/legal/.

    Hàm này không tải lại tài liệu để tránh phụ thuộc vào
    URL download có thể thay đổi hoặc website chặn request.
    """

    documents = get_legal_documents()

    validate_documents(documents)

    print(
        f"Found {len(documents)} legal documents:"
    )

    for index, path in enumerate(
        documents,
        start=1,
    ):
        size_kb = path.stat().st_size / 1024

        print(
            f"  [{index}] {path.name} "
            f"({size_kb:.1f} KB)"
        )

    print(
        "Legal document collection is ready."
    )


def main() -> None:
    setup_directory()
    download_documents()


if __name__ == "__main__":
    main()