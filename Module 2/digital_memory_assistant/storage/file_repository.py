from abc import ABC, abstractmethod
import json
import re
import shutil
from pathlib import Path
from storage.models import StoredFileRecord, now_timestamp
from storage.exceptions import SourceFileNotFoundError, StorageWriteError, StorageDeleteError, FileRecordNotFoundError, InvalidIdentifierError

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")

class StorageBackend(ABC):
    @abstractmethod
    def save(self, source_path, user_id, file_id, original_filename): ...
    @abstractmethod
    def get_record(self, user_id, file_id): ...
    @abstractmethod
    def delete(self, user_id, file_id): ...

class LocalFileSystemStorage(StorageBackend):
    def __init__(self, base_dir: Path | str = Path("data/uploads")) -> None:
        self.base_dir = Path(base_dir)

    def _validate_id(self, value: str) -> None:
        if not _IDENTIFIER.fullmatch(value):
            raise InvalidIdentifierError(f"Invalid identifier: {value!r}")

    def _directory(self, user_id: str, file_id: str) -> Path:
        self._validate_id(user_id)
        self._validate_id(file_id)
        return self.base_dir / user_id / file_id

    def save(self, source_path, user_id, file_id, original_filename):
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise SourceFileNotFoundError(f"Source file not found: {source}")
        try:
            directory = self._directory(user_id, file_id)
            directory.mkdir(parents=True, exist_ok=True)
            stored_filename = file_id + Path(original_filename).suffix
            destination = directory / stored_filename
            shutil.copy2(source, destination)
            record = StoredFileRecord(file_id, user_id, original_filename, stored_filename, str(destination), destination.stat().st_size, now_timestamp())
            (directory / "metadata.json").write_text(json.dumps(record.__dict__, indent=2), encoding="utf-8")
            return record
        except OSError as exc:
            raise StorageWriteError(f"Unable to store file: {source}") from exc

    def get_record(self, user_id, file_id):
        directory = self._directory(user_id, file_id)
        metadata = directory / "metadata.json"
        if not metadata.exists():
            raise FileRecordNotFoundError(f"No record for user={user_id}, file={file_id}")
        try:
            return StoredFileRecord(**json.loads(metadata.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as exc:
            raise FileRecordNotFoundError(f"Unable to read record for user={user_id}, file={file_id}") from exc

    def delete(self, user_id, file_id):
        directory = self._directory(user_id, file_id)
        if not directory.exists():
            raise FileRecordNotFoundError(f"No record for user={user_id}, file={file_id}")
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            raise StorageDeleteError(f"Unable to delete user={user_id}, file={file_id}") from exc
