"""
01_chunking_and_embeddings.py - Metin Parçalama (Chunking) ve Vektörleştirme (Embedding)
----------------------------------------------------------------------------------------
Kariyer hedefi: "RAG mimarileri tasarlamak, Vektör veritabanları konusunda bilgi sahibi olmak"

Öğreneceğimiz Kavramlar:
1. Chunking (Parçalama):
   - Neden yaparız? 100 sayfalık bir PDF'i LLM'e tek parça veremeyiz (maliyet + dikkat kaybı).
   - RecursiveCharacterTextSplitter: Paragrafları, cümleleri ve kelimeleri bölmeden mantıklı kesitler oluşturur.
   - chunk_size: Her parçanın maksimum karakter boyutu.
   - chunk_overlap: Bir parçanın bittiği yer ile diğerinin başladığı yer arasındaki örtüşme payı.
     (Cümle tam ortasından bölündüğünde anlam kaybını önler!).

2. Embedding (Vektör Gömme):
   - Metinlerin anlamını çok boyutlu sayılar dizisine (vektör) dönüştürme.
   - Klasik Arama (Keyword Search): Kelime tam uyuşursa bulur ("araba" ararsan "otomobil"i kaçırabilir).
   - Semantik Arama (Vector Search): Kelimeler farklı olsa bile ANLAMSAL yakınlığı (Cosine Similarity) bulur!
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

from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.embeddings import get_embedding_function
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import numpy as np

console = Console()

def demonstrate_chunking():
    console.print("\n[bold magenta]=== 1. CHUNKING (METİN PARÇALAMA) STRATEJİSİ ===[/bold magenta]")
    
    doc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/sample_company_policy.txt"))
    with open(doc_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    console.print(f"[dim]Orijinal Metin Boyutu: {len(full_text)} karakter[/dim]\n")

    # LangChain'in en popüler metin bölücüsü
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,        # Her parça yaklaşık 300 karakter olsun
        chunk_overlap=50,      # Parçalar arasında 50 karakterlik kesişim payı olsun
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_text(full_text)

    console.print(f"[bold green]Metin {len(chunks)} adet anlamsal parçaya (chunk) bölündü:[/bold green]\n")

    for i, chunk in enumerate(chunks[:3], 1): # İlk 3 parçayı gösterelim
        console.print(Panel(
            chunk.strip(),
            title=f"[cyan]Chunk #{i} ({len(chunk)} karakter)[/cyan]",
            border_style="cyan"
        ))

    console.print("[yellow]💡 Neden chunk_overlap (50 karakter) kullandık?[/yellow]")
    console.print("Eğer bir kural cümlenin tam ortasında iki parçaya bölünürse, bağlam kaybolmasın diye önceki parçanın son 50 karakteri sonraki parçaya da eklenir.\n")

def demonstrate_semantic_embeddings():
    console.print("\n[bold magenta]=== 2. EMBEDDING VE SEMANTİK YAKINLIK (COSINE SIMILARITY) ===[/bold magenta]")
    console.print("Semantik arama, kelimelerin 'sözlük anlamına' değil, 'anlamsal vektör yakınlığına' bakar.\n")

    ef = get_embedding_function()

    # Karşılaştırılacak Cümleler
    target_query = "Siparişim ne zaman kargoya verilir?"
    
    candidates = [
        "Hafta içi saat 16:00'a kadar verilen siparişler aynı gün kargoya verilir.", # Anlamsal olarak AYNI
        "Kargo kolisi hasarlıysa kargo görevlisine hasar tespit tutanağı tutturulmalıdır.", # Kargo ile ilgili ama farklı
        "Kulak içi kulaklıklar hijyen nedeniyle ambalajı açıldıktan sonra iade alınamaz."# Tamamen alakasız
    ]

    console.print(f"[bold white]Hedef Kullanıcı Sorusu:[/bold white] '[bold yellow]{target_query}[/bold yellow]'\n")

    # Vektörleri hesapla
    query_vector = np.array(ef([target_query])[0])
    candidate_vectors = [np.array(v) for v in ef(candidates)]

    def cosine_similarity(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    table = Table(title="Anlamsal Benzerlik Skorları (0.0 ile 1.0 arası)", border_style="green")
    table.add_column("Aday Parça", style="white")
    table.add_column("Cosine Similarity Skoru", justify="center")
    table.add_column("Yorum", style="dim")

    for text, vec in zip(candidates, candidate_vectors):
        score = cosine_similarity(query_vector, vec)
        
        if score > 0.40:
            score_str = f"[bold green]{score:.4f} (En Yüksek)[/bold green]"
            comment = "Doğru Eşleşme! Vektör DB bu parçayı ilk sıraya çeker."
        elif score > 0.15:
            score_str = f"[yellow]{score:.4f} (Orta)[/yellow]"
            comment = "Kargo kelimesi geçiyor ama soruyla tam eşleşmiyor."
        else:
            score_str = f"[red]{score:.4f} (Düşük)[/red]"
            comment = "Tamamen alakasız konu."
            
        table.add_row(text, score_str, comment)

    console.print(table)
    console.print("\n[bold green]İşte RAG'in sihirli gücü buradadır:[/bold green] Müşteri 'ne zaman kargoya verilir' dese de 'kargo gönderim saati'ni matematiksel olarak bulabiliyoruz!\n")

def main():
    demonstrate_chunking()
    demonstrate_semantic_embeddings()

if __name__ == "__main__":
    main()
