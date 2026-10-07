"""
test_agent.py - Otomatik Ajan ve Araç Çağırma Testi
---------------------------------------------------
Tüm yetenekleri (Sipariş, İptal, Stok, RAG) sırayla test eder.
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent_engine import run_agent_turn
from rich.console import Console

console = Console()

def run_tests():
    test_prompts = [
        ("1. Sipariş Sorgulama (Tool Calling)", "10402 nolu siparişim nerede ve ne zaman gelir?"),
        ("2. Sipariş İptali (Mutation Tool Calling)", "10403 nolu siparişimi iptal etmek istiyorum."),
        ("3. Teslim Edilmiş Sipariş İptal Denemesi (Güvenlik)", "10404 nolu siparişimi iptal et."),
        ("4. Stok Kontrolü (Tool Calling)", "Klavyeden stokta var mı, fiyatı ne kadar?"),
        ("5. Agentic RAG (Şirket Politikası Arama)", "Kulaklık aldım, kutusunu açtıktan sonra iade edebilir miyim?"),
        ("6. Agentic RAG (SSS Arama)", "Taksit seçenekleriniz nelerdir?")
    ]

    for title, prompt in test_prompts:
        console.print(f"\n[bold magenta]=== TEST: {title} ===[/bold magenta]")
        console.print(f"[bold white]Kullanıcı:[/bold white] {prompt}")
        response = run_agent_turn(prompt)
        console.print(f"[bold green]Asistan:[/bold green]\n{response}\n")

if __name__ == "__main__":
    run_tests()
