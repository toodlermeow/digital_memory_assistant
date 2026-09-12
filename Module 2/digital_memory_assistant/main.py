import logging
import sys
from ingestion.file_handler import FileHandler

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_file>")
        return 1
    result = FileHandler().ingest_file(sys.argv[1])
    print("File accepted" if result.success else "File rejected")
    print(f"File ID: {result.metadata.file_id}")
    print(f"Filename: {result.metadata.original_filename}")
    print(f"Type: {result.metadata.detected_file_type}")
    print(f"Size: {result.metadata.file_size_bytes} bytes")
    print(f"Status: {result.metadata.processing_status}")
    if result.error_message:
        print(f"Reason: {result.error_message}")
    return 0 if result.success else 1

if __name__ == "__main__":
    raise SystemExit(main())
