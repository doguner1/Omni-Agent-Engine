"""
02_prompt_roles.py - Rol Tabanlı Promptlama & Davranış Yönetimi
-----------------------------------------------------------------
Kariyer hedefi: "Prompt engineering, system prompt tasarımı ve yapay zeka davranış kurguları oluşturmak"

Öğreneceğimiz Kavramlar:
1. Roller (Roles):
   - System: Modelin kimliği, kuralları ve sınırları (Guardrails).
   - User: Kullanıcının girdiği girdi.
   - Assistant / Model: Modelin önceki yanıtı (Hafıza/bağlam oluşturmak için kullanılır).
2. Few-Shot Prompting: Modele birkaç örnek (shot) vererek istediğimiz formatta çıktı almasını sağlama.
3. Structured Output (JSON Formatlama): Modelin her zaman geçerli bir JSON dönmesini sağlama (API entegrasyonları için hayati).
"""

import sys
import os
import json

# Windows UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Proje kök dizinini Python yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import validate_api_keys, get_active_provider, OPENAI_API_KEY, GEMINI_API_KEY
from src.mock_engine import get_mock_completion
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_system_prompt_personalities():
    """
    Aynı soruya farklı SYSTEM promptları verilerek modelin tavrının nasıl değiştiğini inceler.
    """
    console.print("\n[bold magenta]=== 1. System Prompt ile Karakter/Tavır Belirleme ===[/bold magenta]")
    
    question = "Yazılımda döngü (loop) nedir?"
    
    personas = [
        {
            "role_title": "Agresif ve Sabırsız Bir Yazılımcı",
            "system_prompt": "Sen aşırı yoğun, sabırsız ve her şeye sinirlenen kıdemli bir yazılımcısın. Kısa ve ters cevap ver."
        },
        {
            "role_title": "5 Yaşındaki Çocuğa Anlatan İlkokul Öğretmeni",
            "system_prompt": "Sen 5 yaşındaki çocuklara yazılım anlatan çok sevecen bir anaokulu öğretmenisin. Günlük hayattan oyuncak veya oyun benzetmeleri kullan."
        },
        {
            "role_title": "Kurumsal ve Ciddi Müşteri Danışmanı",
            "system_prompt": "Sen kurumsal bir danışmansın. Saygılı, resmi ve teknik terimleri net açıklayan bir üslup kullan."
        }
    ]

    provider = get_active_provider()

    for p in personas:
        console.print(f"\n[cyan]Persona:[/cyan] [bold]{p['role_title']}[/bold]")
        
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": p["system_prompt"]},
                    {"role": "user", "content": question}
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content
        elif provider == "gemini":
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            config = types.GenerateContentConfig(
                system_instruction=p["system_prompt"],
                temperature=0.7
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config=config
            )
            answer = response.text
        else:
            # Mock / Simülasyon
            answer = get_mock_completion(question, system_prompt=p["system_prompt"])

        console.print(Panel(answer, title=p["role_title"], border_style="cyan"))

def test_few_shot_sentiment_analysis():
    """
    Few-Shot Prompting ile modeli bir 'Duygu ve Departman Sınıflandırıcısına' dönüştürür.
    Fine-tuning yapmadan modelin özel bir formatta JSON üretmesini sağlar.
    """
    console.print("\n[bold magenta]=== 2. Yapılandırılmış JSON Çıktısı Alma ===[/bold magenta]")

    system_prompt = """
Sen bir e-ticaret müşteri yorumu analiz sistemisin.
Görevin gelen müşteri yorumunu inceleyip şu JSON formatında cevap vermektir:
{
  "duygu": "Olumlu" | "Olumsuz" | "Nötr",
  "departman": "Kargo" | "Ürün Kalitesi" | "Müşteri Hizmetleri" | "Fiyat",
  "ozet": "Kısa 1 cümlelik özet"
}
SADECE geçerli bir JSON döndür.
"""

    customer_review = "Ürün ertesi gün elime ulaştı ve paketleme harikaydı, ancak kumaşı fotoğraftakine hiç benzemiyor, çok kalitesiz."

    provider = get_active_provider()
    
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": customer_review}
            ],
            temperature=0.0
        )
        raw_output = response.choices[0].message.content
    elif provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.0
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=customer_review,
            config=config
        )
        raw_output = response.text
    else:
        # Mock / Simülasyon
        raw_output = get_mock_completion(customer_review, system_prompt=system_prompt)

    console.print(f"[yellow]Müşteri Yorumu:[/yellow] {customer_review}")
    console.print(Panel(raw_output, title="[bold green]Üretilen Yapılandırılmış JSON[/bold green]", border_style="green"))

def main():
    validate_api_keys()
    test_system_prompt_personalities()
    test_few_shot_sentiment_analysis()

if __name__ == "__main__":
    main()
