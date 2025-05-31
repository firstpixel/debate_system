# markdown_converter_agent.py
"""
Agent for handling user uploads (file, web address, YouTube) and converting them to markdown for RAG ingestion.
"""
import os
import tempfile
import mimetypes
import requests
from urllib.parse import urlparse
from uuid import uuid4
from app.memory_manager import MemoryManager
import sys as _sys
import platform

# Optional: import conversion tools if available
try:
    from docling.parsers import parse_pdf, parse_markdown, parse_text
except ImportError:
    parse_pdf = None
    parse_markdown = None
    parse_text = None
try:
    from markdownify import markdownify as md_html
except ImportError:
    md_html = None
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None
try:
    from github import Github
except ImportError:
    Github = None
try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None

class MarkdownConverterAgent:
    def __init__(self, mem_manager=None):
        self.mem_manager = mem_manager or MemoryManager()

    def ingest(self, user_input, metadata=None, file=None):
        """
        Main entry point. Accepts either a file or a string (URL or text).
        Detects type and routes to the appropriate handler.
        """
        if file is not None:
            return self._handle_file_upload(file, metadata)
        elif self._is_youtube_url(user_input):
            return self._handle_youtube(user_input, metadata)
        elif self._is_github_url(user_input):
            return self._handle_github(user_input, metadata)
        elif self._is_url(user_input):
            return self._handle_web_url(user_input, metadata)
        else:
            return self._handle_text(user_input, metadata)

    def _handle_file_upload(self, file, metadata):
        filename = getattr(file, 'name', None) or metadata.get('title') or 'Uploaded Document'
        ext = os.path.splitext(filename)[-1].lower()
        tmp_dir = os.path.join(os.path.dirname(__file__), '../tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        if DocumentConverter is None:
            return {"status": "error", "reason": "Document upload requires 'docling' package. Please install it.", "title": filename}
        existing_docs = self.mem_manager.get_rag_documents_metadata()
        for doc in existing_docs:
            if doc.get('title') == filename:
                return {"status": "error", "reason": f"A document with the name '{filename}' already exists.", "title": filename}
        try:
            tmp_path = os.path.join(tmp_dir, filename)
            with open(tmp_path, 'wb') as f_out:
                f_out.write(file.read())
            try:
                converter = DocumentConverter()
                result = converter.convert(tmp_path)
                markdown = result.document.export_to_markdown()
            except Exception as e:
                return {"status": "error", "reason": f"Docling conversion failed: {e}", "title": filename}
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            return {"status": "error", "reason": f"File decoding failed: {e}", "title": filename}
        doc_id = str(uuid4())
        meta = {"doc_id": doc_id, "title": filename, **(metadata or {})}
        self.mem_manager.add_rag_document(markdown, meta)
        return {"status": "success", "doc_id": doc_id, "title": filename}

    def _handle_web_url(self, url, metadata):
        if DocumentConverter is None:
            return {"status": "error", "reason": "Web/URL upload requires 'docling' package. Please install it."}
        existing_docs = self.mem_manager.get_rag_documents_metadata()
        for doc in existing_docs:
            if doc.get('source') == url:
                return {"status": "error", "reason": f"A document from this URL already exists."}
        try:
            converter = DocumentConverter()
            result = converter.convert(url)
            markdown = result.document.export_to_markdown()
        except Exception as e:
            return {"status": "error", "reason": f"Docling conversion failed: {e}", "title": url}
        doc_id = str(uuid4())
        meta = {"doc_id": doc_id, "title": url, "source": url, **(metadata or {})}
        self.mem_manager.add_rag_document(markdown, meta)
        return {"status": "success", "doc_id": doc_id, "title": url}

    def _handle_github(self, url, metadata):
        if Github is None:
            return {"status": "error", "reason": "GitHub README ingestion requires 'PyGithub'. Please install it."}
        # Duplicate check by source
        existing_docs = self.mem_manager.get_rag_documents_metadata()
        for doc in existing_docs:
            if doc.get('source') == url:
                return {"status": "error", "reason": f"A document from this GitHub repo already exists."}
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            return {"status": "error", "reason": "Invalid GitHub URL"}
        owner, repo = path_parts[0], path_parts[1]
        g = Github(os.getenv('GITHUB_TOKEN', None))
        repo_obj = g.get_repo(f"{owner}/{repo}")
        readme = repo_obj.get_readme()
        markdown = readme.decoded_content.decode()
        doc_id = str(uuid4())
        meta = {"doc_id": doc_id, "title": f"{owner}/{repo} README", "source": url, **(metadata or {})}
        self.mem_manager.add_rag_document(markdown, meta)
        return {"status": "success", "doc_id": doc_id, "title": f"{owner}/{repo} README"}

    def _handle_youtube(self, url, metadata):
        if YouTubeTranscriptApi is None:
            return {"status": "error", "reason": "YouTube transcript ingestion requires 'youtube-transcript-api'. Please install it."}
        # Duplicate check by source
        existing_docs = self.mem_manager.get_rag_documents_metadata()
        for doc in existing_docs:
            if doc.get('source') == url:
                return {"status": "error", "reason": f"A document from this YouTube video already exists."}
        video_id = self._extract_youtube_id(url)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            return {"status": "error", "reason": f"Could not retrieve transcript: {e}. This may be a temporary YouTube issue or a network problem. Please try again, or check if the video has a transcript available.", "title": f"YouTube {video_id}"}
        if not transcript or not isinstance(transcript, list) or len(transcript) == 0:
            return {"status": "error", "reason": "No transcript available for this YouTube video. It may be disabled, private, or unavailable in your region.", "title": f"YouTube {video_id}"}
        # Markdown: each entry as a paragraph, no timestamps
        markdown = "\n\n".join(entry['text'] for entry in transcript)
        doc_id = str(uuid4())
        meta = {"doc_id": doc_id, "title": f"YouTube {video_id}", "source": url, **(metadata or {})}
        self.mem_manager.add_rag_document(markdown, meta)
        return {"status": "success", "doc_id": doc_id, "title": f"YouTube {video_id}"}

    def _handle_text(self, text, metadata):
        doc_id = str(uuid4())
        meta = {"doc_id": doc_id, **(metadata or {})}
        self.mem_manager.add_rag_document(text, meta)
        return {"status": "success", "doc_id": doc_id, "title": meta.get('title', 'Text')}

    def list_rag_documents(self, limit=100):
        # Use memory_manager to list all unique doc_ids and their metadata
        docs = {}
        for r in self.mem_manager.get_rag_documents_metadata(limit=limit):
            doc_id = r.get('doc_id')
            if doc_id and doc_id not in docs:
                docs[doc_id] = {
                    'doc_id': doc_id,
                    'title': r.get('title'),
                    'source': r.get('source'),
                    'total_chunks': r.get('total_chunks'),
                }
        return list(docs.values())

    @staticmethod
    def _is_url(s):
        try:
            result = urlparse(s)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def _is_youtube_url(s):
        return 'youtube.com' in s or 'youtu.be' in s

    @staticmethod
    def _is_github_url(s):
        return 'github.com' in s

    @staticmethod
    def _extract_youtube_id(url):
        # Handles both youtu.be and youtube.com URLs
        if 'youtu.be' in url:
            return url.split('/')[-1].split('?')[0]
        elif 'youtube.com' in url:
            from urllib.parse import parse_qs
            qs = urlparse(url).query
            params = parse_qs(qs)
            return params.get('v', [None])[0]
        return None
