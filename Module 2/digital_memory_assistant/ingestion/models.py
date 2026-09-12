from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    REJECTED = "rejected"
    FAILED = "failed"

@dataclass
class FileMetadata:
    file_id: str
    original_filename: str
    extension: str
    detected_file_type: Optional[str]
    file_size_bytes: int
    upload_timestamp: str
    processing_status: ProcessingStatus

    @staticmethod
    def now_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

@dataclass
class IngestionResult:
    success: bool
    metadata: FileMetadata
    error_message: Optional[str] = None
