class IngestionError(Exception):
    """Base ingestion exception."""

class FileNotFoundInIngestionError(IngestionError):
    """Raised when the input path does not exist or is not a file."""

class EmptyFileError(IngestionError):
    """Raised when a file contains zero bytes."""

class UnsupportedFileTypeError(IngestionError):
    """Raised when the file extension is unsupported."""

class FileSizeLimitExceededError(IngestionError):
    """Raised when the file exceeds the configured size limit."""

class CorruptedFileError(IngestionError):
    """Raised when content does not match the claimed file type."""
