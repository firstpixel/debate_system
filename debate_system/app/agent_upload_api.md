# Agent Upload API for UI Integration

This document specifies all backend agent methods required for the UI to support uploading and managing documents for Retrieval-Augmented Generation (RAG).

## Methods

### 1. Upload File
- **Method:** `upload_file(file, metadata)`
- **Description:** Accepts a file (PDF, text, markdown, etc.), converts it to markdown, chunks, and ingests into RAG.
- **Parameters:**
  - `file`: Uploaded file object
  - `metadata`: Dict with optional fields (title, source, doc_id, etc.)
- **Returns:** Success/failure, doc_id

### 2. Upload Web Address
- **Method:** `upload_web_address(url, metadata)`
- **Description:** Downloads and converts a web page (HTML, GitHub README, etc.) to markdown, then ingests into RAG.
- **Parameters:**
  - `url`: String (web address)
  - `metadata`: Dict with optional fields
- **Returns:** Success/failure, doc_id

### 3. Upload YouTube Video
- **Method:** `upload_youtube_video(url, metadata)`
- **Description:** Fetches transcript from YouTube, formats as markdown, and ingests into RAG.
- **Parameters:**
  - `url`: String (YouTube video address)
  - `metadata`: Dict with optional fields
- **Returns:** Success/failure, doc_id

### 4. List RAG Documents
- **Method:** `list_rag_documents()`
- **Description:** Returns a list of all documents currently stored in the RAG Qdrant collection, with metadata (doc_id, title, source, etc.).
- **Returns:** List of dicts (one per document)

### 5. (Optional) Delete RAG Document
- **Method:** `delete_rag_document(doc_id)`
- **Description:** Removes a document and all its chunks from the RAG collection.
- **Parameters:**
  - `doc_id`: String
- **Returns:** Success/failure

---

## UI Integration Notes
- UI should provide buttons/fields for file upload, web address, and YouTube video.
- UI should display the list of all RAG documents (with metadata) in the sidebar, alongside debate config.
- UI should allow document deletion (optional).
- All uploads should be markdownified and chunked before ingestion.
