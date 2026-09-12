class StorageError(Exception):
    """Base storage exception."""

class SourceFileNotFoundError(StorageError): pass
class StorageWriteError(StorageError): pass
class StorageDeleteError(StorageError): pass
class FileRecordNotFoundError(StorageError): pass
class InvalidIdentifierError(StorageError): pass
