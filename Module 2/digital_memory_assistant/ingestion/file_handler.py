import logging
import uuid
from pathlib import Path
from ingestion.exceptions import IngestionError
from ingestion.models import FileMetadata, IngestionResult, ProcessingStatus
from ingestion.validator import FileValidator

logger = logging.getLogger(__name__)

class FileHandler:
    """Coordinates validation and metadata creation for one uploaded file."""
    def __init__(self, validator: FileValidator | None = None) -> None:
        self.validator = validator or FileValidator()

    def ingest_file(self, file_path: str) -> IngestionResult:
        path = Path(file_path)
        file_id = str(uuid.uuid4())
        metadata = FileMetadata(file_id, path.name, path.suffix.lower(), None, 0, FileMetadata.now_timestamp(), ProcessingStatus.UPLOADED)
        try:
            detected_type, size_bytes = self.validator.validate(path)
            metadata.detected_file_type = detected_type
            metadata.file_size_bytes = size_bytes
            metadata.processing_status = ProcessingStatus.VALIDATED
            return IngestionResult(True, metadata, None)
        except IngestionError as exc:
            metadata.processing_status = ProcessingStatus.REJECTED
            logger.warning("File rejected: %s", exc)
            return IngestionResult(False, metadata, str(exc))
        except Exception as exc:
            metadata.processing_status = ProcessingStatus.FAILED
            logger.exception("Unexpected error while ingesting %s", path)
            return IngestionResult(False, metadata, str(exc))
