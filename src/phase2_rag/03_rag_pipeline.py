"""
03_rag_pipeline.py - Uçtan Uca RAG (Retrieval-Augmented Generation) Hattı
------------------------------------------------------------------------
Kariyer hedefi: "RAG mimarileri tasarlamak ve canlı ortamlarda kullanıma almak"

Öğreneceğimiz Kavramlar:
1. RAG'in 3 Temel Adımı:
   - R (Retrieve - Bilgiyi Çek): Kullanıcı sorusunu vektöre çevirip Vektör DB'den en alakalı paragrafları çekmek.
   - A (Augment - Zenginleştir): Bu paragrafları sistem komutuna (Prompt) "Bağlam (Context)" olarak eklemek.
   - G (Generate - Üret): LLM'e "Sadece bu bağlama göre cevap ver" diyerek halüsinasyonsuz yanıt ürettirmek.

2. Halüsinasyon (Hallucination) Önleme:
   - Genel model TeknoMarket'in özel kargo kodunu ("TR-TEKNO-77") asla bilemez. Ya uydurur ya da bilmediğini söyler.
   - RAG ile modele şirket hafızası kazandırılır!
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
from src.config import validate_api_keys, get_active_provider, OPENAI_API_KEY, GEMINI_API_KEY
from src.embeddings import get_embedding_function
from src.mock_engine import simulate_stream
from rich.console import Console
from rich.panel import Panel

console = Console()

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chroma_data"))

def get_chroma_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    ef = get_embedding_function()
    return client.get_collection(name="company_knowledge", embedding_function=ef)

def ask_with_rag(question: str):
    console.print(f"\n[bold green]====================================================[/bold green]")
    console.print(f"[bold cyan]❓ KULLANICI SORUSU:[/bold cyan] [bold white]'{question}'[/bold white]")
    console.print(f"[bold green]====================================================[/bold green]\n")

    # 1. RETRIEVE (Vektör Veritabanından Alakalı Bilgileri Çek)
    collection = get_chroma_collection()
    results = collection.query(query_texts=[question], n_results=2)
    retrieved_docs = results["documents"][0]

    context_text = "\n---\n".join(retrieved_docs)

    console.print(Panel(
        context_text,
        title="[bold yellow]1. RETRIEVE AŞAMASI: ChromaDB'den Çekilen İlgili Paragraflar (Context)[/bold yellow]",
        border_style="yellow"
    ))

    # 2. AUGMENT (Promptu Bağlam ile Zenginleştir)
    augmented_prompt = f"""
Aşağıda şirketimize ait resmi bilgi dokümanları verilmiştir:
========================================
{context_text}
========================================

Kullanıcı Sorusu: {question}

TALİMAT:
1. SADECE yukarıdaki dokümanda yazan bilgilere dayanarak cevap ver.
2. Eğer dokümanda cevap açıkça yoksa, "Dokümanlarımızda bu konu hakkında bilgi bulunmamaktadır." de.
3. Kendi genel bilginden şirket kuralı uydurma (Halüsinasyon engeli).
"""

    # 3. GENERATE (Yanıtı Üret)
    provider = get_active_provider()
    console.print(f"[bold blue]2. GENERATE AŞAMASI: Model Yanıtı Üretiyor ({provider.upper()})...[/bold blue]\n")

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": augmented_prompt}],
            temperature=0.0
        )
        answer = response.choices[0].message.content
    elif provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        config = types.GenerateContentConfig(temperature=0.0)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=augmented_prompt,
            config=config
        )
        answer = response.text
    else:
        # Mock / Simülasyon Yanıtı
        if "kulaklık" in question.lower():
            answer = (
                "Şirket politikamız gereğince, kulak içi kulaklıklar hijyen kuralları "
                "ve telif hakları nedeniyle ambalajı bir kez açıldıktan sonra maalesef iade alınamamaktadır."
            )
        elif "tamir" in question.lower() or "kargo kodu" in question.lower() or "arıza" in question.lower():
            answer = (
                "Arızalı cihazınızı teknik servisimize ücretsiz göndermek için "
                "'TR-TEKNO-77' kargo kodunu kullanarak anlaşmalı kargo firmamızla gönderim yapabilirsiniz. "
                "Yasal onarım süremiz azami 20 iş günüdür."
            )
        else:
            answer = "Şirket politikalarımıza göre ilgili süreç başarıyla uygulanmaktadır."

    console.print(Panel(answer, title="[bold green]RAG İle Üretilen Doğrulanmış Yanıt[/bold green]", border_style="green"))

def main():
    validate_api_keys()

    # Gerçek dünya senaryoları:
    test_questions = [
        "Kulak içi kulaklık aldım kutusunu açıp denedim ama beğenmedim, iade edebilir miyim?",
        "Bozulan telefonumu servise yollayacağım, ücretsiz kargo kodu var mı?"
    ]

    for q in test_questions:
        ask_with_rag(q)

if __name__ == "__main__":
    main()
