"""
03_cli_chatbot.py - Bellek (Chat History) Yönetimli Etkileşimli Sohbet Botu
--------------------------------------------------------------------------
Kariyer hedefi: "AI destekli chatbot çözümleri geliştirmek, kullanıcı deneyimi süreçlerini iyileştirmek"

Öğreneceğimiz Kavramlar:
1. LLM'lerin Durumsuz (Stateless) Doğası:
   - LLM'ler hiçbir şeyi kendiliğinden "hatırlamaz".
   - Bir botun konuşmayı hatırlaması için, geçmişteki TÜM konuşma geçmişini (messages listesi)
     her istekte modele tekrar göndermemiz gerekir.
2. Context Window (Bağlam Penceresi) Yönetimi:
   - Sonsuz sohbet geçmişi göndermek hem token limitini doldurur hem de maliyeti katlar.
   - Bu yüzden "Son N mesajı saklama" (Sliding Window) stratejisini uyguluyoruz.
3. Etkileşimli Arayüz:
   - Konsolda kullanıcı ile canlı sohbet döngüsü (loop).
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

from src.config import validate_api_keys, get_active_provider, OPENAI_API_KEY, GEMINI_API_KEY
from src.mock_engine import get_mock_completion, simulate_stream
from rich.console import Console

console = Console()

# Sohbet geçmişinde tutulacak maksimum mesaj sayısı (Sliding Window)
MAX_HISTORY_MESSAGES = 10

def start_chatbot():
    validate_api_keys()
    provider = get_active_provider()
    
    console.print("[bold green]====================================================[/bold green]")
    console.print("[bold cyan]AI Müşteri Destek Asistanı (CLI Chatbot)[/bold cyan]")
    console.print(f"[dim]Aktif Sağlayıcı: {provider.upper()} | Bellek Boyutu: Son {MAX_HISTORY_MESSAGES} mesaj[/dim]")
    console.print("[dim]Komutlar: 'cikis' veya 'exit' ile sonlandır, 'temizle' ile hafızayı sıfırla[/dim]")
    console.print("[bold green]====================================================\n[/bold green]")

    system_instruction = (
        "Sen 'TeknoMarket' isimli e-ticaret şirketinin yardımsever, kibar ve teknik bilgisi yüksek "
        "müşteri destek asistanısın. Türkçe yanıt ver ve kullanıcının sorularına net, pratik çözümler sun."
    )

    # Sohbet Geçmişi (Chat History)
    history = []

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    elif provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

    while True:
        try:
            user_input = input("\n[Siz]: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Görüşme sonlandırıldı.[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["cikis", "çıkış", "exit", "quit"]:
            console.print("[bold green]Görüşmek üzere, iyi günler dileriz![/bold green]")
            break

        if user_input.lower() in ["temizle", "clear"]:
            history.clear()
            if provider == "gemini":
                chat_session = client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                )
            console.print("[bold yellow]Sohbet geçmişi (hafıza) temizlendi![/bold yellow]")
            continue

        console.print("[bold cyan][Asistan]:[/bold cyan] ", end="")

        if provider == "openai":
            messages = [{"role": "system", "content": system_instruction}]
            messages.extend(history[-MAX_HISTORY_MESSAGES:])
            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                stream=True
            )

            assistant_reply = ""
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                assistant_reply += content
            print()

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": assistant_reply})

        elif provider == "gemini":
            response = chat_session.send_message_stream(user_input)
            for chunk in response:
                text = chunk.text or ""
                print(text, end="", flush=True)
            print()

        else:
            # Mock / Simülatör Modu
            assistant_reply = get_mock_completion(user_input, system_prompt=system_instruction)
            for chunk in simulate_stream(assistant_reply):
                print(chunk, end="", flush=True)
            print()
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": assistant_reply})

if __name__ == "__main__":
    start_chatbot()
