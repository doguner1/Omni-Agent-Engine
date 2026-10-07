"""
02_vector_store_chroma.py - ChromaDB Vektör Veritabanı ve Semantik Arama
--------------------------------------------------------------------------
Kariyer hedefi: "Vektör veritabanları (Pinecone, Weaviate, Qdrant, Chroma vb.) konusunda bilgi sahibi olmak"

Öğreneceğimiz Kavramlar:
1. Vektör Veritabanı (Vector DB) Mimarisi:
   - Klasik Veritabanı (PostgreSQL, MySQL): Kelime eşleşmesi (SELECT * FROM docs WHERE text LIKE '%iade%')
   - Vektör Veritabanı (ChromaDB): Anlamsal benzerlik araması (ANN - Approximate Nearest Neighbors).
2. Collection (Koleksiyon):
   - SQL'deki "Table" kavramının Vektör DB'deki karşılığıdır.
3. Persistent Storage (Kalıcı Depolama):
   - Vektörleri bellekte (RAM) geçici tutmak yerine diske kaydetme.
   - Böylece 10.000 sayfalık bir dökümanı her uygulama başladığında tekrar embedding yapıp para/zaman harcamayız!
4. Metadata & Filtering:
   - Parçalara etiket ekleme (Örn: `{"kategori": "iade", "kaynak": "politika.txt"}`).
"""

import sys
import os

# Windows UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Proje kök dizinini Python yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import chromadb
from src.embeddings import get_embedding_function
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.table import Table

console = Console()

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chroma_data"))

def initialize_vector_db():
    console.print("\n[bold magenta]=== CHROMADB VEKTÖR VERİTABANI OLUŞTURMA & VERİ YÜKLEME ===[/bold magenta]")
    
    # 1. Kalıcı Disk İstemcisi Oluştur (PersistentClient)
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Güvenilir yerel embedding fonksiyonumuz
    ef = get_embedding_function()
    
    # 2. 'company_knowledge' koleksiyonunu oluştur veya getir
    collection = client.get_or_create_collection(
        name="company_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Dokümanı oku
    doc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/sample_company_policy.txt"))
    with open(doc_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Parçala (Chunking)
    splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=30)
    chunks = splitter.split_text(full_text)

    # Koleksiyonu sıfırla ve yeniden ekle
    existing_count = collection.count()
    if existing_count > 0:
        ids_to_del = [f"chunk_{i}" for i in range(existing_count)]
        try:
            collection.delete(ids=ids_to_del)
        except Exception:
            pass

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": "sample_company_policy.txt", "chunk_id": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

    console.print(f"[bold green]✓ {len(chunks)} adet chunk başarıyla ChromaDB'ye kaydedildi.[/bold green]")
    console.print(f"[dim]Veritabanı Konumu: {DB_DIR}[/dim]\n")
    return collection

def search_in_vector_db(collection, query: str, top_k: int = 2):
    console.print(f"[bold cyan]🔍 Kullanıcı Araması:[/bold cyan] '[bold yellow]{query}[/bold yellow]'")
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    docs = results["documents"][0]
    distances = results["distances"][0]
    metas = results["metadatas"][0]

    table = Table(title=f"En Benzer İlk {top_k} Parça (Top-{top_k} Retrieval)", border_style="cyan")
    table.add_column("Sıra", justify="center", style="bold")
    table.add_column("Cosine Distance (0'a yakın = Çok Benzer)", justify="center")
    table.add_column("Bulunan Belge İçeriği", style="white")

    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metas), 1):
        similarity_percentage = max(0, (1.0 - dist) * 100)
        table.add_row(
            str(i),
            f"{dist:.4f} (%{similarity_percentage:.1f} Yakınlık)",
            doc.strip()
        )

    console.print(table)
    console.print("\n")

def main():
    collection = initialize_vector_db()

    # Farklı konularda semantik arama testleri yapalım:
    test_queries = [
        "Kulaklık aldım, ambalajını açtım, iade edebilir miyim?",
        "Bozuk cihazımı tamire göndermek için kargo kodu nedir?",
        "1500 liralık sipariş versem kargo parası öder miyim?"
    ]

    for q in test_queries:
        search_in_vector_db(collection, q, top_k=2)

if __name__ == "__main__":
    main()
