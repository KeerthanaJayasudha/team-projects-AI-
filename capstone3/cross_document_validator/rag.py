"""RAG layer with FAISS vector store."""

import uuid
import numpy as np
from typing import List, Optional, Dict, Tuple
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from cross_document_validator.models import DocumentContent, ChunkWithMetadata
from cross_document_validator.exceptions import RAGError

"""RAG layer with FAISS vector store."""


class RAGLayer:
    """RAG layer for document chunking, embedding, and retrieval using FAISS."""
    
    def __init__(self, embedding_model: str, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize FAISS vector store and embedding model.
        
        Args:
            embedding_model: Name of the OpenAI embedding model (e.g., 'text-embedding-ada-002')
            chunk_size: Maximum size of text chunks in characters
            overlap: Number of overlapping characters between consecutive chunks
        """
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize OpenAI embeddings
        try:
            self.embeddings = OpenAIEmbeddings(model=embedding_model)
        except Exception as e:
            raise RAGError(f"Failed to initialize embedding model: {e}")
        
        # Initialize FAISS index (will be created when first document is added)
        self.index: Optional[faiss.IndexFlatL2] = None
        self.dimension: Optional[int] = None
        
        # Metadata storage: chunk_id -> (document_id, document_type, chunk_text, chunk_index)
        self.chunk_metadata: Dict[str, Tuple[str, str, str, int]] = {}
        
        # Mapping from FAISS index position to chunk_id
        self.index_to_chunk_id: Dict[int, str] = {}
        
        # Counter for FAISS index positions
        self.next_index_position = 0
    
    async def chunk_and_store(self, document: DocumentContent) -> None:
        """
        Split document into chunks and store in FAISS.
        
        Args:
            document: Document with text and metadata
            
        Raises:
            RAGError: If chunking or storage fails
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(document.text)
            
            if not chunks:
                raise RAGError(f"No chunks generated from document {document.document_id}")
            
            # Generate embeddings for all chunks
            try:
                embeddings = await self.embeddings.aembed_documents(chunks)
            except Exception as e:
                raise RAGError(f"Failed to generate embeddings for document {document.document_id}: {e}")
            
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)

            # Initialize FAISS index if this is the first document
            if self.index is None:
                self.dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatL2(self.dimension)
            
            # Verify embedding dimensions match
            if embeddings_array.shape[1] != self.dimension:
                raise RAGError(
                    f"Embedding dimension mismatch: expected {self.dimension}, "
                    f"got {embeddings_array.shape[1]}"
                )
            
            # Add embeddings to FAISS index
            self.index.add(embeddings_array)
            
            # Store metadata for each chunk
            for chunk_index, chunk_text in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                
                # Store metadata
                self.chunk_metadata[chunk_id] = (
                    document.document_id,
                    document.document_type,
                    chunk_text,
                    chunk_index
                )
                
                # Map FAISS index position to chunk_id
                self.index_to_chunk_id[self.next_index_position] = chunk_id
                self.next_index_position += 1
                
        except RAGError:
            raise
        except Exception as e:
            raise RAGError(f"Failed to chunk and store document {document.document_id}: {e}")
    
    async def retrieve_chunks(
        self,
        query: str,
        top_k: int = 5,
        filter_document_type: Optional[str] = None
    ) -> List[ChunkWithMetadata]:
        """
        Retrieve most relevant chunks based on query.
        
        Args:
            query: Search query text
            top_k: Number of chunks to retrieve
            filter_document_type: Optional filter by document type
            
        Returns:
            List of chunks with metadata and similarity scores
            
        Raises:
            RAGError: If retrieval fails
        """
        try:
            # Check if index is initialized
            if self.index is None or self.index.ntotal == 0:
                return []
            
            # Generate query embedding
            try:
                query_embedding = await self.embeddings.aembed_query(query)
            except Exception as e:
                raise RAGError(f"Failed to generate query embedding: {e}")
            
            # Convert to numpy array
            query_array = np.array([query_embedding], dtype=np.float32)

            # Normalize query embedding
            faiss.normalize_L2(query_array)
            
            # Verify dimension
            if query_array.shape[1] != self.dimension:
                raise RAGError(
                    f"Query embedding dimension mismatch: expected {self.dimension}, "
                    f"got {query_array.shape[1]}"
                )
            
            # Retrieve more chunks than needed if filtering is required
            # This ensures we have enough chunks after filtering
            search_k = min(top_k * 3 if filter_document_type else top_k, self.index.ntotal)
            
            # Search FAISS index
            distances, indices = self.index.search(query_array, search_k)
            
            # Convert results to ChunkWithMetadata
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                # Get chunk_id from index position
                chunk_id = self.index_to_chunk_id.get(int(idx))
                
                if chunk_id is None:
                    continue
                
                # Get metadata
                metadata = self.chunk_metadata.get(chunk_id)
                if metadata is None:
                    continue
                
                document_id, document_type, chunk_text, chunk_index = metadata
                
                # Apply document_type filter if specified
                if filter_document_type and document_type != filter_document_type:
                    continue
                
                # Convert L2 distance to cosine similarity
                # For normalized vectors: cosine_similarity = 1 - (L2_distance^2 / 2)
                # Since OpenAI embeddings are normalized, we can use this conversion
                similarity_score = float(1.0 - (distance / 2.0))
                
                # Clamp similarity score to [0, 1] range
                similarity_score = max(0.0, min(1.0, similarity_score))
                
                results.append(ChunkWithMetadata(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    document_type=document_type,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    similarity_score=similarity_score
                ))
                
                # Stop if we have enough results
                if len(results) >= top_k:
                    break
            
            return results
            
        except RAGError:
            raise
        except Exception as e:
            raise RAGError(f"Failed to retrieve chunks: {e}")


