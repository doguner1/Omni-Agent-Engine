"""
01_simple_llm.py - İlk LLM Entegrasyonu ve Temel Parametreler
---------------------------------------------------------------
Kariyer hedefi: "LLM tabanlı uygulamalar geliştirmek, performans ve kullanıcı deneyimi süreçlerini iyileştirmek"

Öğreneceğimiz Kavramlar:
1. LLM Çağrısı (Generation / Completion): Modele bir metin verip yanıt alma süreci.
2. Temperature:
   - 0.0: Deterministik, mantıklı, tutarlı (RAG, kod yazma, veri analizi için ideal).
   - 0.7 - 1.0: Yaratıcı, hikaye yazımı, beyin fırtınası.
3. Max Tokens / Output Limits: Modelin üretebileceği maksimum token (kelime parçası) sınırı.
4. Streaming (Akış): Yanıtın kelime kelime gelmesi (Kullanıcının boş ekrana bakmasını engeller, UX için kritiktir).
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
from src.mock_engine import get_mock_completion, simulate_stream, MockResponse
from rich.console import Console
from rich.panel import Panel

console = Console()

def call_mock(prompt: str, temperature: float = 0.7, stream: bool = False):
    console.print(f"[bold cyan]Model:[/bold cyan] AI Simülatörü (Mock Model)")
    console.print(f"[bold yellow]Parametreler:[/bold yellow] Temperature={temperature}, Streaming={stream}\n")
    
    full_text = get_mock_completion(prompt, temperature=temperature)
    
    if stream:
        console.print("[bold green]Cevap (Akış halinde):[/bold green] ", end="")
        for chunk in simulate_stream(full_text):
            print(chunk, end="", flush=True)
        print("\n")
        return full_text
    else:
        mock_resp = MockResponse(full_text)
        console.print(Panel(full_text, title="[bold green]Model Cevabı[/bold green]", border_style="green"))
        usage = mock_resp.usage
        console.print(f"[dim]Kullanılan Tokenlar -> Prompt: {usage.prompt_tokens}, Cevap: {usage.completion_tokens}, Toplam: {usage.total_tokens}[/dim]\n")
        return full_text

def call_openai(prompt: str, temperature: float = 0.7, stream: bool = False):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    console.print(f"[bold cyan]Model:[/bold cyan] OpenAI (gpt-4o-mini)")
    console.print(f"[bold yellow]Parametreler:[/bold yellow] Temperature={temperature}, Streaming={stream}\n")
    
    if stream:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True
        )
        console.print("[bold green]Cevap (Akış halinde):[/bold green] ", end="")
        full_text = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            full_text += content
        print("\n")
        return full_text
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        answer = response.choices[0].message.content
        console.print(Panel(answer, title="[bold green]Model Cevabı[/bold green]", border_style="green"))
        usage = response.usage
        console.print(f"[dim]Kullanılan Tokenlar -> Prompt: {usage.prompt_tokens}, Cevap: {usage.completion_tokens}, Toplam: {usage.total_tokens}[/dim]\n")
        return answer

def call_gemini(prompt: str, temperature: float = 0.7, stream: bool = False):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(temperature=temperature)
    model_name = "gemini-2.5-flash"

    console.print(f"[bold cyan]Model:[/bold cyan] Google Gemini ({model_name})")
    console.print(f"[bold yellow]Parametreler:[/bold yellow] Temperature={temperature}, Streaming={stream}\n")
    
    if stream:
        response = client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
            config=config
        )
        console.print("[bold green]Cevap (Akış halinde):[/bold green] ", end="")
        full_text = ""
        for chunk in response:
            text = chunk.text or ""
            print(text, end="", flush=True)
            full_text += text
        print("\n")
        return full_text
    else:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        console.print(Panel(response.text, title="[bold green]Model Cevabı[/bold green]", border_style="green"))
        return response.text

def main():
    validate_api_keys()
    provider = get_active_provider()
    prompt = "Yapay zeka alanında çalışan bir yazılımcının bilmesi gereken en önemli 3 kavramı 2'şer cümle ile açıkla."

    console.print(Panel(f"[bold white]{prompt}[/bold white]", title="[bold magenta]Gönderilen Prompt[/bold magenta]", border_style="magenta"))

    # 1. Normal Çağrı (Streaming = False)
    console.print("[bold blue]== 1. Standart Çağrı (Sonuç tek parça halinde gelir) ==[/bold blue]")
    if provider == "openai":
        call_openai(prompt, temperature=0.2, stream=False)
    elif provider == "gemini":
        call_gemini(prompt, temperature=0.2, stream=False)
    else:
        call_mock(prompt, temperature=0.2, stream=False)

    # 2. Akış Çağrısı (Streaming = True)
    console.print("[bold blue]== 2. Streaming Çağrısı (Gerçek zamanlı kelime kelime gelir) ==[/bold blue]")
    if provider == "openai":
        call_openai(prompt, temperature=0.7, stream=True)
    elif provider == "gemini":
        call_gemini(prompt, temperature=0.7, stream=True)
    else:
        call_mock(prompt, temperature=0.7, stream=True)

if __name__ == "__main__":
    main()
