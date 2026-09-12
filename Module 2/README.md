# Digital Memory Assistant — Module 2

## File Ingestion, Validation and Storage System

Module 2 of the **Digital Memory Assistant** establishes the file-management foundation required to safely accept, validate, store, retrieve, and delete user-uploaded files.

The module takes a raw file and moves it through a controlled pipeline:

```text
User File
   ↓
File Ingestion
   ↓
File Validation
   ↓
Accepted / Rejected
   ↓
StorageService
   ↓
Local File Storage
   ↓
Metadata
```

The goal is to ensure that only valid, supported, non-empty, size-compliant files move forward into later processing modules.

---

## 1. What Module 2 Is Used For

This module is the **input and storage foundation** of the Digital Memory Assistant.

It is responsible for:

- Receiving a file path through the ingestion layer
- Checking whether the file exists
- Rejecting empty files
- Checking supported extensions
- Enforcing a maximum file size
- Checking actual file signatures (magic bytes) for PDFs and images
- Checking UTF-8 decodability for text files
- Creating structured metadata for every ingestion attempt
- Assigning a UUID-based file ID
- Storing valid files on the local filesystem
- Saving metadata in `metadata.json`
- Retrieving stored file information
- Deleting stored files and metadata
- Returning clear, structured results instead of exposing raw validation exceptions to the CLI/application
- Providing automated tests for validation and storage behavior

---

## 2. Module Structure

The supplied Module 2 package contains:

```text
digital_memory_assistant/
├── main.py
│
├── ingestion/
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   ├── models.py
│   ├── validator.py
│   └── file_handler.py
│
├── storage/
│   ├── __init__.py
│   ├── models.py
│   ├── exceptions.py
│   ├── file_repository.py
│   └── storage_service.py
│
├── tests/
│   ├── __init__.py
│   ├── test_validator.py
│   └── test_storage.py
│
├── sample_files/
│   ├── notes.pdf
│   ├── notes.txt
│   ├── photo.jpg
│   ├── screenshot.png
│   ├── archive.docx
│   └── fake.pdf
│
└── data/
    └── uploads/
        └── student42/
            └── .gitkeep
```

The complete original Module 2 implementation is also provided in the uploaded ZIP in this folder.

---

# 3. Ingestion Layer

The `ingestion` package is responsible for deciding whether an incoming file is acceptable.

Its public entry point is:

```python
FileHandler.ingest_file()
```

The ingestion flow is deliberately separated into two responsibilities:

```text
FileHandler
    ↓
coordinates the process

FileValidator
    ↓
performs individual validation checks
```

This separation makes the code easier to test and extend.

---

## 4. `ingestion/config.py`

This file contains the configurable ingestion rules.

### Maximum file size

The current limit is:

```text
20 MB
```

It is also converted into bytes for the actual comparison:

```python
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
```

### Supported extensions

The module currently supports:

| Extension | Internal Type |
|---|---|
| `.pdf` | `PDF` |
| `.png` | `IMAGE` |
| `.jpg` | `IMAGE` |
| `.jpeg` | `IMAGE` |
| `.txt` | `TEXT` |

### Supported MIME types

The configuration also defines expected MIME types for the supported categories. MIME detection is informational in the current validator; file validity is primarily checked using extension rules and content signatures.

### Staging directory

`UPLOAD_STAGING_DIR` is defined as a future configuration point. The current local storage implementation uses its own storage directory instead.

---

# 5. `ingestion/validator.py`

`FileValidator` is responsible only for validation.

The checks run in this deliberate order:

```text
1. Existence
      ↓
2. Not empty
      ↓
3. Supported extension
      ↓
4. Size limit
      ↓
5. Content signature
```

Cheap checks are performed before reading file content.

## Validation 1 — Existence

The validator checks that the path exists and points to a real file.

If not, it raises:

```text
FileNotFoundInIngestionError
```

## Validation 2 — Empty file

A file with zero bytes is rejected using:

```text
EmptyFileError
```

The file size is returned from this check so the application does not need to perform another size lookup.

## Validation 3 — Extension

The extension is converted to lowercase and checked against the supported extension list.

An unsupported extension raises:

```text
UnsupportedFileTypeError
```

## Validation 4 — Size

Files larger than the configured 20 MB limit raise:

```text
FileSizeLimitExceededError
```

## Validation 5 — Content signature

The validator reads the first 16 bytes of the file.

Known signatures include:

```text
PDF  → %PDF-
PNG  → 89 50 4E 47 0D 0A 1A 0A
JPEG → FF D8 FF
```

This prevents a file from being accepted only because its filename has a valid extension.

For example:

```text
fake.pdf
```

containing ordinary text is rejected because its content does not start with the expected PDF signature.

For `.txt` files, there is no magic signature, so the validator checks whether the beginning of the file can be decoded as UTF-8.

---

# 6. `ingestion/models.py`

This file defines the structured objects returned by the ingestion layer.

## `ProcessingStatus`

The possible lifecycle states are:

```text
UPLOADED
VALIDATED
REJECTED
FAILED
```

Meaning:

- `UPLOADED` — the file has been received and a metadata object has been created.
- `VALIDATED` — all validation checks passed.
- `REJECTED` — a known validation rule failed.
- `FAILED` — an unexpected system error occurred.

## `FileMetadata`

Contains:

```text
file_id
original_filename
extension
detected_file_type
file_size_bytes
upload_timestamp
processing_status
```

The timestamp is generated in UTC and stored as an ISO 8601 string.

## `IngestionResult`

This is the final result returned by `FileHandler.ingest_file()`.

It contains:

```text
success
metadata
error_message
```

This allows the caller to handle accepted and rejected files without having to inspect raw exceptions.

---

# 7. `ingestion/exceptions.py`

Custom exceptions are used so callers can distinguish different validation failures.

The base exception is:

```text
IngestionError
```

Specific exceptions are:

```text
FileNotFoundInIngestionError
EmptyFileError
UnsupportedFileTypeError
FileSizeLimitExceededError
CorruptedFileError
```

For example, an unsupported `.docx` file raises `UnsupportedFileTypeError`, while an oversized file raises `FileSizeLimitExceededError`.

This is cleaner and safer than making application code parse error-message strings.

---

# 8. `ingestion/file_handler.py`

`FileHandler` is the orchestrator of the ingestion layer.

Its main method is:

```python
ingest_file(file_path)
```

The method:

1. Converts the input into a `Path`.
2. Generates a UUID for the file ID.
3. Extracts the original filename and extension.
4. Creates initial metadata with `UPLOADED` status.
5. Calls `FileValidator.validate()`.
6. If validation succeeds, updates metadata to `VALIDATED`.
7. If a known ingestion error occurs, changes status to `REJECTED` and returns the error message.
8. If an unexpected error occurs, changes status to `FAILED`, logs the exception, and still returns a structured `IngestionResult`.

This means the CLI or a future API endpoint can call one method and always receive a structured result instead of needing a large `try/except` block.

The validator is also injectable through the constructor, which supports testing and future replacement with another validator implementation.

---

# 9. Storage Layer

The storage layer is responsible for keeping accepted files and their metadata.

The architecture is:

```text
Application
     ↓
StorageService
     ↓
StorageBackend
     ↓
LocalFileSystemStorage
     ↓
Local Disk
```

This abstraction means the rest of the application does not have to depend directly on the local filesystem implementation.

---

# 10. `storage/file_repository.py`

This file defines the storage contract and local implementation.

## `StorageBackend`

An abstract interface with three operations:

```python
save(source_path, user_id, file_id, original_filename)
get_record(user_id, file_id)
delete(user_id, file_id)
```

## `LocalFileSystemStorage`

The current concrete implementation stores files under:

```text
data/uploads
```

The directory layout is:

```text
data/uploads/<user_id>/<file_id>/
├── <file_id>.<extension>
└── metadata.json
```

Example:

```text
data/uploads/student42/file123/
├── file123.pdf
└── metadata.json
```

---

# 11. Safe Identifiers

`user_id` and `file_id` are validated before they are used in filesystem paths.

The allowed identifier pattern is effectively:

```text
A-Z
a-z
0-9
_
-
```

This prevents unsafe values such as:

```text
../../etc
```

from being used to escape the intended storage directory.

This is an important filesystem-safety measure.

---

# 12. Saving a File

When `save()` is called:

1. The source path is checked.
2. The user ID and file ID are validated.
3. A destination directory is created.
4. The source is copied using `shutil.copy2()`.
5. A `StoredFileRecord` is created.
6. `metadata.json` is written beside the stored file.

The original source file is not deleted or modified by the storage operation.

The stored filename is based on the file ID rather than the original filename. The original filename is retained in metadata.

This prevents collisions when multiple files have the same original name.

---

# 13. `storage/models.py`

The main storage model is:

```text
StoredFileRecord
```

It contains:

| Field | Purpose |
|---|---|
| `file_id` | Identifier of the stored file |
| `user_id` | Owner/user identifier |
| `original_filename` | Filename supplied by the user |
| `stored_filename` | Filename used inside storage |
| `storage_path` | Path to the stored file |
| `file_size` | File size in bytes |
| `created_at` | UTC creation timestamp |

This model is a dataclass and is easy to serialize to JSON.

---

# 14. `storage/storage_service.py`

`StorageService` is the application-facing storage interface.

It exposes:

```python
store_file()
get_file_info()
delete_file()
```

By default it uses `LocalFileSystemStorage`.

The important design benefit is that higher-level application code can depend on `StorageService` instead of knowing how files are physically stored.

For example, a future cloud implementation could provide another `StorageBackend` while the application continues using the same service-level operations.

---

# 15. `storage/exceptions.py`

Storage failures use dedicated exceptions:

```text
StorageError
SourceFileNotFoundError
StorageWriteError
StorageDeleteError
FileRecordNotFoundError
InvalidIdentifierError
```

This gives the caller a clear distinction between a missing source file, a missing stored record, an unsafe identifier, and an actual storage operation failure.

---

# 16. Command-Line Interface

`main.py` provides a simple way to manually test ingestion.

Run:

```bash
python main.py <path_to_file>
```

Example:

```bash
python main.py sample_files/notes.pdf
```

The CLI configures logging, creates a `FileHandler`, and prints the ingestion result.

---

# 17. Expected Output — Valid File

A successful run prints information similar to:

```text
File accepted
File ID: <generated UUID>
Filename: notes.pdf
Type: PDF
Size: <file size> bytes
Status: ProcessingStatus.VALIDATED
```

The exact UUID and file size depend on the input file.

The important result is that the file is accepted and metadata is returned.

The CLI exits with:

```text
0
```

for success.

---

# 18. Expected Output — Invalid File

For a rejected file, the CLI prints information similar to:

```text
File rejected
File ID: <generated UUID>
Filename: archive.docx
Type: None
Size: 0 bytes
Status: ProcessingStatus.REJECTED
Reason: Unsupported file extension '.docx' ...
```

The exact reason depends on the validation failure.

The CLI exits with:

```text
1
```

for failure/rejection.

This makes the CLI useful for both manual testing and shell/automation workflows.

---

# 19. Examples of Rejected Inputs

| Input | Expected Result | Reason |
|---|---|---|
| Valid PDF | Accepted | Passes all checks |
| Valid PNG | Accepted | Passes all checks |
| Valid JPEG | Accepted | Passes all checks |
| Valid TXT | Accepted | Valid UTF-8 text |
| `.docx` | Rejected | Unsupported extension |
| Missing path | Rejected | File does not exist |
| File > 20 MB | Rejected | Size limit exceeded |
| Fake `.pdf` | Rejected | PDF signature mismatch |
| Invalid image content | Rejected | PNG/JPEG signature mismatch |
| Empty file | Rejected | Zero bytes |

---

# 20. Automated Tests

The module includes tests for both ingestion/validation and storage.

Run the test suite with:

```bash
pytest
```

## `tests/test_validator.py`

The validation tests cover:

- Valid PDF acceptance
- Valid PNG acceptance
- Valid JPEG acceptance
- Valid TXT acceptance
- Unsupported `.docx` rejection
- Missing file rejection
- Oversized file rejection
- Fake/corrupted PDF rejection
- Corrupted image rejection
- Empty file rejection
- Direct testing of the specific custom exceptions

The tests use temporary directories and generated test content, so they do not need to modify real user files.

## `tests/test_storage.py`

The storage tests cover:

- Successful storage
- Correct IDs and filenames
- File size and storage path
- Stored content matching the source
- Source file remaining intact
- Duplicate original filenames not colliding
- Successful metadata retrieval
- Unknown file retrieval failure
- Successful deletion
- Metadata and stored file removal
- Unknown file deletion failure
- Missing source-file handling
- Storage write failure handling

Temporary storage directories are used so tests remain isolated.

---

# 21. Complete End-to-End Flow

Consider a user uploading:

```text
college_notes.pdf
```

The process is:

```text
college_notes.pdf
        ↓
FileHandler.ingest_file()
        ↓
Generate file_id
        ↓
Create initial metadata
        ↓
FileValidator.validate()
        ↓
Check existence
        ↓
Check empty file
        ↓
Check extension
        ↓
Check 20 MB limit
        ↓
Check PDF signature
        ↓
VALIDATED
        ↓
StorageService.store_file()
        ↓
LocalFileSystemStorage.save()
        ↓
data/uploads/<user_id>/<file_id>/
        ├── <file_id>.pdf
        └── metadata.json
```

The application now has both the physical file and structured information about it.

---

# 22. Why This Architecture Is Useful

### Separation of responsibilities

Validation, orchestration, storage, models, and exceptions are separated into clear components.

### Safer filesystem handling

Identifiers are restricted before being used to construct paths.

### Better error handling

Specific exceptions allow callers to distinguish different failures.

### No filename collisions

Files are stored using unique file IDs instead of relying on original filenames.

### Testability

The validator and storage layers can be tested independently.

### Extensibility

The `StorageBackend` abstraction allows future storage implementations.

### Maintainability

The rest of the application can use `StorageService` without being tightly coupled to the local filesystem.

---

# 23. Future Integration

Module 2 is designed to be the foundation for future Digital Memory Assistant modules.

A larger architecture can eventually become:

```text
User
 ↓
File Upload
 ↓
Module 2
Ingestion + Validation + Storage
 ↓
Valid Stored File
 ↓
Document Processing
 ↓
Text Extraction / OCR
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Storage
 ↓
Semantic Search
 ↓
AI Assistant / Question Answering
```

Module 2 itself does **not** implement OCR, embeddings, vector search, or AI question answering. Its role is to make sure the incoming files are valid, safely identified, and available for those later stages.

---

# 24. Current Limitations

The current implementation uses local filesystem storage.

It does not currently provide:

- Cloud object storage
- User authentication
- OCR
- PDF text extraction
- Embedding generation
- Vector database integration
- Semantic search
- AI question answering
- Full document indexing

These can be introduced in later modules.

---

# 25. Possible Future Improvements

Potential improvements include:

- S3 or another cloud object-storage backend
- More complete MIME/content validation
- Virus/malware scanning before storage
- File checksum/hash generation
- Persistent database records for metadata
- Resumable or streaming uploads
- More supported document formats
- Stronger PDF/image integrity checks
- Authentication and authorization around user IDs
- Integration with document extraction and AI processing pipelines

The existing storage abstraction provides a good boundary for introducing alternative storage implementations.

---

# 26. Module 2 Summary

Module 2 provides the **file ingestion, validation, and storage foundation** of the Digital Memory Assistant.

In simple terms:

> **Module 2 takes a raw user file, checks whether it is valid and supported, assigns it an identity, stores it safely, records its metadata, and provides operations to retrieve or delete it later.**

The main components are:

```text
Ingestion
   +
Validation
   +
Metadata
   +
Storage
   +
Exception Handling
   +
Testing
```

This creates a reliable boundary between raw uploaded files and the future document-processing and AI capabilities of the project.
