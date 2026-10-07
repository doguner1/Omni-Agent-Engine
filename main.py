"""
main.py - Omni-Agent Framework Ana Çalıştırma Noktası
-----------------------------------------------------
Kullanım:
    python main.py

Özellikler:
- Tak-çalıştır Bilgi Tabanı (RAG)
- Otomatik Araç Çağırma (Tool / Function Calling)
- Canlı / Simülasyon modları desteği
- Zengin terminal arayüzü
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

from src.config import validate_api_keys, get_active_provider
from src.agent_engine import run_agent_turn
from custom_tools.registry import tool_registry
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def print_welcome_banner():
    provider = get_active_provider()
    
    tools = tool_registry.get_all_tools()
    
    console.print(Panel(
        f"[bold white]OMNI-AGENT: KURUMSAL YAPAY ZEKA ASİSTANI[/bold white]\n"
        f"[dim]Mod: {provider.upper()} | Yüklü Araç Sayısı: {len(tools)}[/dim]\n\n"
        "[green]✓ Bilgi Tabanı (RAG): Aktif ('search_knowledge_base')[/green]\n"
        "[green]✓ Dış Sistem API'ları: Aktif ('get_order_status', 'cancel_order', 'check_product_stock')[/green]\n\n"
        "[yellow]İpuçları:[/yellow]\n"
        "• Sipariş sorabilirsiniz: [cyan]'10402 nolu kargom nerede?'[/cyan]\n"
        "• İptal isteyebilirsiniz: [cyan]'10403 nolu siparişimi iptal et'[/cyan]\n"
        "• Şirket kuralı sorabilirsiniz: [cyan]'Kulaklık açıldıktan sonra iade edilir mi?'[/cyan]\n"
        "• Stok sorabilirsiniz: [cyan]'Klavyeden kaç tane var?'[/cyan]\n"
        "• Çıkmak için: [red]'cikis'[/red]",
        title="[bold green]🚀 Omni-Agent Engine[/bold green]",
        border_style="green"
    ))

def start_interactive_session():
    validate_api_keys()
    print_welcome_banner()

    history = []

    while True:
        try:
            user_input = input("\n[Siz]: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Görüşme sonlandırıldı.[/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["cikis", "çıkış", "exit", "quit"]:
            console.print("[bold green]İyi günler dileriz![/bold green]")
            break

        if user_input.lower() in ["araclar", "tools"]:
            table = Table(title="Kullanılabilir Araçlar (Tools)", border_style="cyan")
            table.add_column("Araç Adı", style="bold cyan")
            table.add_column("Açıklama", style="white")
            for t in tool_registry.get_all_tools():
                table.add_row(t["name"], t["description"])
            console.print(table)
            continue

        console.print("[bold cyan][Omni-Agent Düşünüyor...][/bold cyan]")
        response = run_agent_turn(user_input, history)
        
        console.print(Panel(response, title="[bold green]Asistan Yanıtı[/bold green]", border_style="green"))

if __name__ == "__main__":
    start_interactive_session()
