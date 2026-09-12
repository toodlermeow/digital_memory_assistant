from ingestion.config import MAX_FILE_SIZE_BYTES
from ingestion.exceptions import CorruptedFileError, EmptyFileError, FileSizeLimitExceededError, UnsupportedFileTypeError
from ingestion.file_handler import FileHandler
from ingestion.models import ProcessingStatus
from ingestion.validator import FileValidator
from storage.exceptions import FileRecordNotFoundError, SourceFileNotFoundError
from storage.file_repository import LocalFileSystemStorage
from storage.storage_service import StorageService


def test_valid_pdf_is_accepted(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")
    result = FileHandler().ingest_file(str(path))
    assert result.success is True
    assert result.metadata.detected_file_type == "PDF"
    assert result.metadata.processing_status == ProcessingStatus.VALIDATED


def test_supported_images_and_text(tmp_path):
    png = tmp_path / "image.png"; png.write_bytes(b"\x89PNG\r\n\x1a\n")
    jpg = tmp_path / "image.jpg"; jpg.write_bytes(b"\xff\xd8\xff")
    txt = tmp_path / "notes.txt"; txt.write_text("hello", encoding="utf-8")
    validator = FileValidator()
    assert validator.validate(png)[0] == "IMAGE"
    assert validator.validate(jpg)[0] == "IMAGE"
    assert validator.validate(txt)[0] == "TEXT"


def test_invalid_inputs_are_rejected(tmp_path):
    unsupported = tmp_path / "archive.docx"; unsupported.write_bytes(b"data")
    fake_pdf = tmp_path / "fake.pdf"; fake_pdf.write_text("not a pdf")
    empty = tmp_path / "empty.txt"; empty.write_bytes(b"")
    huge = tmp_path / "huge.txt"; huge.write_bytes(b"a" * (MAX_FILE_SIZE_BYTES + 1))
    validator = FileValidator()
    for path, error in [(unsupported, UnsupportedFileTypeError), (fake_pdf, CorruptedFileError), (empty, EmptyFileError), (huge, FileSizeLimitExceededError)]:
        try:
            validator.validate(path)
            assert False
        except error:
            pass


def test_storage_round_trip_and_delete(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("Digital Memory Assistant", encoding="utf-8")
    service = StorageService(LocalFileSystemStorage(tmp_path / "uploads"))
    record = service.store_file(source, "student42", "file123", "notes.txt")
    assert service.get_file_info("student42", "file123").file_id == "file123"
    assert source.exists()
    assert tmp_path.joinpath("uploads/student42/file123/file123.txt").read_text() == "Digital Memory Assistant"
    service.delete_file("student42", "file123")
    try:
        service.get_file_info("student42", "file123")
        assert False
    except FileRecordNotFoundError:
        pass


def test_missing_source_is_rejected(tmp_path):
    service = StorageService(LocalFileSystemStorage(tmp_path / "uploads"))
    try:
        service.store_file(tmp_path / "missing.txt", "u", "f", "missing.txt")
        assert False
    except SourceFileNotFoundError:
        pass
