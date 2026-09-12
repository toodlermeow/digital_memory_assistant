from pathlib import Path
from storage.file_repository import LocalFileSystemStorage

class StorageService:
    """Application-facing wrapper around a pluggable storage backend."""
    def __init__(self, backend=None) -> None:
        self.backend = backend or LocalFileSystemStorage()

    def store_file(self, source_path: str | Path, user_id: str, file_id: str, original_filename: str):
        return self.backend.save(source_path, user_id, file_id, original_filename)

    def get_file_info(self, user_id: str, file_id: str):
        return self.backend.get_record(user_id, file_id)

    def delete_file(self, user_id: str, file_id: str) -> None:
        self.backend.delete(user_id, file_id)
