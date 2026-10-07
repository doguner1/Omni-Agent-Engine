"""
Yapılandırma Modülü (config.py)
---------------------------------
Bu dosya ortam değişkenlerini (.env) okur ve projenin hangi LLM sağlayıcısını (Gemini, OpenAI veya Mock)
kullanacağını otomatik olarak belirler.

Profesyonel AI projelerinde "Model Agnostic" (modele bağımlı olmayan) bir mimari kurmak çok önemlidir.
Böylece müşteri veya şirket OpenAI yerine Gemini ya da açık kaynak bir model istediğinde
tüm kodları baştan yazmak zorunda kalmazsınız.
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Windows terminallerinde Türkçe karakter ve Emoji desteğini güvenceye al (UTF-8)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env dosyasını otomatik olarak yükle
load_dotenv()

# API Anahtarlarını al (boşlukları temizle)
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
ANTHROPIC_API_KEY = (os.getenv("ANTHROPIC_API_KEY") or "").strip()

# Varsayılan Sağlayıcı Belirleme
DEFAULT_PROVIDER = (os.getenv("DEFAULT_PROVIDER") or "").strip().lower()

def get_active_provider() -> str:
    """
    Kullanılabilir API anahtarlarına ve tercihe göre aktif sağlayıcıyı döner.
    API anahtarı bulunamazsa geliştirme/öğrenme sürecinin kesintiye uğramaması için
    'mock' (Simülasyon Modu) döner.
    """
    if DEFAULT_PROVIDER == "gemini" and GEMINI_API_KEY:
        return "gemini"
    if DEFAULT_PROVIDER == "openai" and OPENAI_API_KEY:
        return "openai"
    
    # Otomatik algılama
    if GEMINI_API_KEY:
        return "gemini"
    if OPENAI_API_KEY:
        return "openai"
    if ANTHROPIC_API_KEY:
        return "anthropic"
        
    # Anahtar henüz eklenmemişse eğitim simülasyon modu aktifleşir
    return "mock"

def validate_api_keys() -> None:
    """
    API anahtarlarının durumunu kontrol eder ve bilgilendirme yapar.
    """
    provider = get_active_provider()
    if provider == "mock":
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel(
            "[bold yellow]⚠️ SİMÜLASYON (MOCK) MODU AKTİF[/bold yellow]\n\n"
            "Henüz bir API anahtarı eklenmediği için kodlar [bold cyan]Yapay Zeka Simülatörü[/bold cyan] ile çalışıyor.\n"
            "Tüm akış, prompt mantığı, token hesaplamaları ve çıktılar birebir simüle edilir.\n"
            "Dilediğiniz zaman [bold green].env[/bold green] dosyasına gerçek [bold green]GEMINI_API_KEY[/bold green] bilginizi eklediğinizde\n"
            "sistem hiçbir kod değişikliği gerektirmeden otomatik olarak canlı Gemini 2.5 Flash modeline geçecektir.",
            title="[bold yellow]Bilgilendirme[/bold yellow]",
            border_style="yellow"
        ))
