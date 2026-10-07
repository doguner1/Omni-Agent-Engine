"""
vector_store.py - Vektör Veritabanı Arama Servisi
--------------------------------------------------
ChromaDB üzerinde kayıtlı bilgi tabanında semantik arama yapar ve
sonuçları metin olarak döner. Agentic RAG için 'search_knowledge_base'
aracı bu fonksiyonu kullanır.
"""

import os
from pathlib import Path
import chromadb
from src.embeddings import get_embedding_function

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "chroma_data"

def query_knowledge_base(query: str, top_k: int = 2) -> str:
    """Bilgi tabanından en alakalı parçaları bulup birleştirir."""
    if not DB_DIR.exists():
        return "Bilgi tabanı henüz oluşturulmamış. Lütfen önce 'python ingest.py' çalıştırın."
        
    client = chromadb.PersistentClient(path=str(DB_DIR))
    ef = get_embedding_function()
    
    try:
        collection = client.get_collection(name="company_knowledge", embedding_function=ef)
    except Exception:
        return "Bilgi tabanı koleksiyonu bulunamadı. Lütfen 'python ingest.py' çalıştırın."

    results = collection.query(query_texts=[query], n_results=top_k)
    docs = results["documents"][0]
    
    if not docs:
        return "Bu konuda bilgi tabanında ilgili döküman bulunamadı."
        
    return "\n---\n".join(docs)
