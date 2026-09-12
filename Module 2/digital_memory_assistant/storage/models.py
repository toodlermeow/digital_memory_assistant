from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class StoredFileRecord:
    file_id: str
    user_id: str
    original_filename: str
    stored_filename: str
    storage_path: str
    file_size: int
    created_at: str

def now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
