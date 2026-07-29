from pathlib import Path

from app.services.document_extractor import DocumentExtractor


def main() -> None:
    extractor = DocumentExtractor()

    file_path = Path(
        r"C:\Users\saeed\Desktop\sop0.docx"
    )

    result = extractor.extract(file_path)

    print("Page count:", result.page_count)
    print("Metadata:", result.metadata)
    print("Text length:", len(result.text))
    print()
    print("Text preview:")
    print(result.text[:1000])


if __name__ == "__main__":
    main()