"""
ingest.py - Otomatik Bilgi Tabanı İndeksleyici (Tak-Çalıştır RAG)
-----------------------------------------------------------------
Kullanım:
    python ingest.py

Ne İşe Yarar?
    'knowledge_base/' klasörüne attığınız tüm PDF, TXT ve MD dosyalarını otomatik olarak tarar,
    parçalar (chunking), anlamsal vektörlere dönüştürür (embedding) ve ChromaDB'ye kaydeder.
    
    Herhangi bir şirket belgesi, ürün listesi veya kullanım kılavuzunu klasöre atıp bu komutu
    çalıştırmanız yapay zekayı o verilerle "eğitmek" için yeterlidir!
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Windows UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Proje bileşenleri
from src.embeddings import get_embedding_function

console = Console()

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
DB_DIR = BASE_DIR / "chroma_data"

def read_file_content(file_path: Path) -> str:
    """Desteklenen dosya formatlarını (txt, md, pdf) okur."""
    ext = file_path.suffix.lower()
    
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
        except Exception as e:
            console.print(f"[bold red]PDF okuma hatası ({file_path.name}): {e}[/bold red]")
            return ""
            
    return ""

def run_ingestion():
    console.print(Panel(
        "[bold cyan]📚 OMNI-AGENT BİLGİ TABANI İNDEKSLEME BAŞLADI[/bold cyan]\n"
        f"Hedef Klasör: [white]{KNOWLEDGE_DIR}[/white]\n"
        f"Vektör Veritabanı: [white]{DB_DIR}[/white]",
        title="[bold green]Ingest / Eğitim Süreci[/bold green]",
        border_style="green"
    ))

    if not KNOWLEDGE_DIR.exists():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        console.print("[yellow]knowledge_base klasörü oluşturuldu. Lütfen içine döküman ekleyin.[/yellow]")
        return

    # Desteklenen dosyaları bul
    supported_extensions = [".txt", ".md", ".pdf"]
    files = [f for f in KNOWLEDGE_DIR.iterdir() if f.suffix.lower() in supported_extensions]

    if not files:
        console.print(f"[bold red]Uyarı:[/bold red] '{KNOWLEDGE_DIR}' klasöründe indekslenecek dosya (.txt, .md, .pdf) bulunamadı.")
        return

    # ChromaDB başlat
    client = chromadb.PersistentClient(path=str(DB_DIR))
    ef = get_embedding_function()
    
    collection = client.get_or_create_collection(
        name="company_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    # Eski kayıtları temizle (temiz indeksleme)
    try:
        count = collection.count()
        if count > 0:
            ids = [f"id_{i}" for i in range(count)]
            collection.delete(ids=ids)
    except Exception:
        pass

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )

    all_chunks = []
    all_metadatas = []
    all_ids = []
    summary_data = []

    global_id = 0
    for file_path in files:
        content = read_file_content(file_path)
        if not content.strip():
            continue

        chunks = splitter.split_text(content)
        summary_data.append((file_path.name, len(content), len(chunks)))

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": file_path.name,
                "chunk_index": i
            })
            all_ids.append(f"doc_{global_id}")
            global_id += 1

    if all_chunks:
        collection.add(
            documents=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids
        )

    # Rapor tablosu oluştur
    table = Table(title="İndekslenen Dokümanlar Raporu", border_style="cyan")
    table.add_column("Dosya Adı", style="bold white")
    table.add_column("Karakter Sayısı", justify="right")
    table.add_column("Oluşturulan Parça (Chunk)", justify="right", style="green")

    for name, chars, chunks_count in summary_data:
        table.add_row(name, f"{chars:,}", str(chunks_count))

    console.print(table)
    console.print(f"\n[bold green]✓ Toplam {len(all_chunks)} parça başarıyla vektörleştirildi ve kaydedildi![/bold green]")
    console.print("[dim]Yapay zeka artık bu dökümanlardaki tüm sorulara RAG ile cevap verebilir.[/dim]\n")

if __name__ == "__main__":
    run_ingestion()
