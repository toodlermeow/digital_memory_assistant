import mimetypes
from pathlib import Path
from ingestion.config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from ingestion.exceptions import (FileNotFoundInIngestionError, EmptyFileError, UnsupportedFileTypeError, FileSizeLimitExceededError, CorruptedFileError)

PDF_SIGNATURE = b"%PDF-"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
SIGNATURE_READ_SIZE = 16

class FileValidator:
    def validate_existence(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise FileNotFoundInIngestionError(f"No file found at path: {path}")

    def validate_not_empty(self, path: Path) -> int:
        size = path.stat().st_size
        if size == 0:
            raise EmptyFileError(f"File is empty (0 bytes): {path.name}")
        return size

    def validate_extension(self, path: Path) -> str:
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Unsupported file extension '{extension}'. Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}")
        return SUPPORTED_EXTENSIONS[extension]

    def validate_size(self, size_bytes: int) -> None:
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise FileSizeLimitExceededError(f"File size {size_bytes:,} bytes exceeds the {MAX_FILE_SIZE_MB}MB limit ({MAX_FILE_SIZE_BYTES:,} bytes).")

    def validate_content_signature(self, path: Path, expected_type: str) -> None:
        with path.open("rb") as f:
            header = f.read(SIGNATURE_READ_SIZE)
        if expected_type == "PDF" and not header.startswith(PDF_SIGNATURE):
            raise CorruptedFileError(f"File '{path.name}' has a .pdf extension but its content does not start with the PDF signature ({PDF_SIGNATURE!r}).")
        if expected_type == "IMAGE" and not (header.startswith(PNG_SIGNATURE) or header.startswith(JPEG_SIGNATURE)):
            raise CorruptedFileError(f"File '{path.name}' has an image extension but its content does not match the PNG or JPEG signature.")
        if expected_type == "TEXT":
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise CorruptedFileError(f"File '{path.name}' has a .txt extension but its content could not be decoded as UTF-8 text.") from exc

    def get_mime_type(self, path: Path) -> str | None:
        return mimetypes.guess_type(str(path))[0]

    def validate(self, path: Path) -> tuple[str, int]:
        self.validate_existence(path)
        size_bytes = self.validate_not_empty(path)
        detected_type = self.validate_extension(path)
        self.validate_size(size_bytes)
        self.validate_content_signature(path, detected_type)
        return detected_type, size_bytes
