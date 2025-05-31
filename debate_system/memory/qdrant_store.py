# memory/qdrant_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance, UpdateResult
from uuid import uuid4
from typing import List
from memory.embeddings import embed_text
import os
import re

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "debate_memory"
COLLECTION_NAME_DOC = "debate_memory_documents"
RAG_CHUNK_SIZE = 1000  # Default chunk size for RAG document chunks (tokens/words)

class LTMStore:
    def __init__(self, collection_name=COLLECTION_NAME, vector_size=768):
        self.collection = collection_name
        self.vector_size = vector_size
        self.client = QdrantClient(url=QDRANT_URL)


        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        collections = self.client.get_collections().collections
        if self.collection not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
    
    def store_memory(self, agent_id: str, text: str, tags: List[str]):
        embedding = embed_text(text)
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={"agent_id": agent_id, "text": text, "tags": tags}
        )
        self.client.upsert(collection_name=self.collection, points=[point])
        
    # deprecated
    def add_memory(self, agent_id: str, text: str, tags: List[str]):
        embedding = embed_text(text)
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={"agent_id": agent_id, "text": text, "tags": tags}
        )
        self.client.upsert(collection_name=self.collection, points=[point])


    def get_relevant(self, agent_id: str, top_k: int = 5) -> str:
        query_vector = embed_text(agent_id + " memory")
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=Filter(
                must=[FieldCondition(key="agent_id", match=MatchValue(value=agent_id))]
            )
        )
        return "\n".join([hit.payload["text"] for hit in results])
    
    def query_ltm(self, agent_id: str, limit: int = 5) -> str:
        # LTM: agent-specific retrieval
        results, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter={"must": [{"key": "agent_id", "match": {"value": agent_id}}]},
            limit=limit
        )
        return "\n".join(r.payload.get("text", "") for r in results)

class RAGRetriever:
    def __init__(self, collection_name=COLLECTION_NAME_DOC, chunk_size=RAG_CHUNK_SIZE):
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection = collection_name
        self.vector_size = 768
        self.chunk_size = chunk_size
        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        collections = self.client.get_collections().collections
        if self.collection not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )

    def add_document(self, markdown_text: str, metadata: dict = None, chunk_size: int = None):
        """
        Add a markdown document, automatically chunking by subtitle and hard limit.
        metadata: dict with doc-level metadata (e.g., doc_id, title, source, etc.)
        chunk_size: max tokens per chunk (default: RAG_CHUNK_SIZE or 1000)
        """
        chunk_size = chunk_size or self.chunk_size
        chunks = self.chunk_markdown(markdown_text, max_tokens=chunk_size)
        doc_id = metadata.get("doc_id") if metadata else str(uuid4())
        title = metadata.get("title") if metadata else None
        source = metadata.get("source") if metadata else None
        for idx, chunk in enumerate(chunks):
            chunk_metadata = {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}_{idx}",
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "title": title,
                "source": source,
                **(metadata or {})
            }
            embedding = embed_text(chunk)
            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={"text": chunk, **chunk_metadata}
            )
            self.client.upsert(collection_name=self.collection, points=[point])

    import re

    def chunk_markdown(self, md_text, max_tokens=400, overlap=200, tokenizer=None):
        """
        Chunk markdown with optional fallback to fixed-length with overlap.
        - Primary: split by headers and paragraphs, observing token limits.
        - Fallback: if no headings, use fixed-length with token overlap.
        - Safety guard: injects artificial paragraph breaks in very long blocks.
        """

        def count_tokens(text):
            return len(text.split()) if tokenizer is None else len(tokenizer.encode(text))

        def fixed_length_chunks(text):
            words = text.split()
            chunks = []
            start = 0
            while start < len(words):
                end = min(start + max_tokens, len(words))
                chunk = " ".join(words[start:end])
                chunks.append(chunk.strip())
                start += max_tokens - overlap  # overlap control
            return chunks

        def force_fake_paragraphs(text, max_words_per_para=80):
            """
            If a block of text has no paragraph breaks, force one every N words.
            """
            words = text.split()
            fake_paragraphs = []
            for i in range(0, len(words), max_words_per_para):
                fake_paragraphs.append(" ".join(words[i:i + max_words_per_para]))
            return "\n\n".join(fake_paragraphs)

        # Primary split: detect markdown headers
        sections = re.split(r'(#+ .+)', md_text)
        if len(sections) == 1:
            # No headings found → fallback
            return fixed_length_chunks(md_text)

        chunks = []
        current_chunk = ""
        current_tokens = 0

        i = 0
        while i < len(sections):
            if re.match(r'(#+ .+)', sections[i]):
                subtitle = sections[i].strip()
                text = sections[i + 1].strip() if i + 1 < len(sections) else ""

                # Inject fake paragraph breaks if needed
                if '\n\n' not in text and count_tokens(text) > max_tokens:
                    text = force_fake_paragraphs(text)

                section_text = f"{subtitle}\n{text}"
                section_tokens = count_tokens(section_text)

                if section_tokens > max_tokens:
                    # Split section text by paragraph with overlap
                    paragraphs = text.split('\n\n')
                    temp_chunk = subtitle + "\n"
                    temp_tokens = count_tokens(temp_chunk)
                    for para in paragraphs:
                        para = para.strip()
                        if not para:
                            continue
                        para_tokens = count_tokens(para)
                        if temp_tokens + para_tokens > max_tokens:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = subtitle + "\n" + para + "\n"
                            temp_tokens = count_tokens(temp_chunk)
                        else:
                            temp_chunk += para + "\n\n"
                            temp_tokens += para_tokens
                    if temp_chunk.strip():
                        chunks.append(temp_chunk.strip())
                else:
                    if current_tokens + section_tokens > max_tokens:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = section_text + "\n\n"
                        current_tokens = section_tokens
                    else:
                        current_chunk += section_text + "\n\n"
                        current_tokens += section_tokens
                i += 2
            else:
                i += 1

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


    def query_text(self, query: str, top_k: int = 5) -> str:
        vector = embed_text(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k
        )
        return "\n".join([r.payload["text"] for r in results])

    def query_rag(self, limit: int = 5) -> str:
        # RAG: global document retrieval, no agent_id
        results, _ = self.client.scroll(
            collection_name=self.collection,
            limit=limit
        )
        return "\n".join(r.payload.get("text", "") for r in results)

    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks belonging to a document by doc_id from the RAG collection.
        Returns the number of deleted points.
        """
        result: UpdateResult = self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
        )
        return getattr(result, "operation_count", 0)
