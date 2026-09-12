from pathlib import Path

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf": "PDF", ".png": "IMAGE", ".jpg": "IMAGE", ".jpeg": "IMAGE", ".txt": "TEXT"}
SUPPORTED_MIME_TYPES = {"PDF": ["application/pdf"], "IMAGE": ["image/png", "image/jpeg"], "TEXT": ["text/plain"]}
UPLOAD_STAGING_DIR = Path("uploads_staging")
