from langchain_community.document_loaders import PyPDFLoader
from agent.setup.chroma_db.chroma_setup import get_chroma_client, get_or_create_collection
from sentence_transformers import SentenceTransformer
import re
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class FAQProcessor:
    def __init__(self):
        """Initialize the FAQ processor with ChromaDB client and embedding model."""
        self.chroma_client = get_chroma_client()
        self.collection = get_or_create_collection(self.chroma_client)
        
        self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    def split_faq_pairs(self, text: str) -> List[str]:
        """
        Split the FAQ document into Q/A chunks using numbering pattern.
        One chunk = one complete FAQ answer.
        """
        pattern = r"(\d+\.\s+.*?)(?=\d+\.\s+|\Z)"

        matches = re.findall(pattern, text, flags=re.DOTALL)

        chunks = []
        for m in matches:
            chunk = m.strip()
            if len(chunk) > 0:
                chunks.append(chunk)

        return chunks

    async def process_pdf(self, pdf_path: str, filename: str) -> Dict:
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            full_text = "\n".join([p.page_content for p in pages])
            faq_chunks = self.split_faq_pairs(full_text)
            documents = []
            metadatas = []
            ids = []

            for i, chunk_text in enumerate(faq_chunks):
                documents.append(chunk_text)
                metadatas.append({
                    "filename": filename,
                    "chunk_index": i
                })
                ids.append(f"{filename}_chunk_{i}")

            embeddings = self.embedding_model.encode(documents).tolist()

            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            return {
                "success": True,
                "filename": filename,
                "total_pages": len(pages),
                "total_chunks": len(faq_chunks),
                "message": f"Successfully processed {filename} with Q/A chunking"
            }

        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "message": f"Failed to process {filename}: {str(e)}"
            }

    # SEARCH

    def search_similar_documents(self, query: str, n_results: int = 4) -> Dict:
        try:
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            return results

        except Exception as e:
            print(f"Search error: {e}")
            return {}


    # CLEAR COLLECTION
 
    def clear_collection(self):
        try:
            self.chroma_client.delete_collection(name="faq_documents")
            self.collection = get_or_create_collection(self.chroma_client)
            return {"success": True, "message": "Collection cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # STATS

    def get_collection_stats(self) -> Dict:
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            return {"error": str(e)}
