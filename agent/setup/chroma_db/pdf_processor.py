from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agent.setup.chroma_db.chroma_setup import get_chroma_client, get_or_create_collection
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class FAQProcessor:
    def __init__(self):
        """Initialize the FAQ processor with ChromaDB client and sentence transformers."""
        self.chroma_client = get_chroma_client()
        self.collection = get_or_create_collection(self.chroma_client)
        
        # Load sentence transformer model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def process_pdf(self, pdf_path: str, filename: str) -> Dict:
        """
        Process a PDF file: extract text, chunk it, embed, and store in ChromaDB.
        
        Args:
            pdf_path: Path to the PDF file
            filename: Original filename for metadata
            
        Returns:
            dict with processing statistics
        """
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(pages)
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                documents.append(chunk.page_content)
                metadatas.append({
                    "filename": filename,
                    "chunk_index": i
                })
                ids.append(f"{filename}_chunk_{i}")
            
            # Generate embeddings using sentence-transformers
            embeddings_list = self.embedding_model.encode(documents).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                documents=documents,
                embeddings=embeddings_list,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "filename": filename,
                "total_pages": len(pages),
                "total_chunks": len(chunks),
                "message": f"Successfully processed {filename} and stored in ChromaDB"
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "message": f"Failed to process {filename}: {str(e)}"
            }
    
    def search_similar_documents(self, query: str, n_results: int = 4) -> Dict:
        """
        Search for similar documents in ChromaDB.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Dict with search results
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search in ChromaDB using embeddings
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            self.chroma_client.delete_collection(name="faq_documents")
            self.collection = get_or_create_collection(self.chroma_client)
            return {"success": True, "message": "Collection cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            return {"error": str(e)}
