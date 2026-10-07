"""
agent_engine.py - Omni-Agent Yürütücü ve Tool Calling Motoru
-------------------------------------------------------------
Kariyer hedefi: "AI Agent, tool calling, function calling ve AI workflow yönetimi"

Öğreneceğimiz Kavramlar:
1. ReAct (Reasoning + Acting) Mimarisi:
   - Model kullanıcı sorusunu analiz eder.
   - Hangi aracın (Tool) çağrılması gerektiğine karar verir (Reasoning).
   - Aracı parametreleriyle birlikte tetikler (Acting).
   - Dönen sonucu alıp kullanıcıya anlaşılır bir dilde açıklar.

2. Agentic RAG:
   - Bilgi tabanı aramasını sabit bir pipeline yapmak yerine bir "Tool" olarak modele veririz.
   - Böylece model selamlama için boşuna arama yapmaz; sadece bilgi gerektiğinde arar!
"""

import sys
import os
import re
import json
from typing import Dict, Any, List, Optional

# Windows UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import get_active_provider, OPENAI_API_KEY, GEMINI_API_KEY
from custom_tools.registry import tool_registry
from rich.console import Console
from rich.panel import Panel

console = Console()

SYSTEM_PROMPT = """
Sen TeknoMarket şirketinin akıllı ve yetkili Müşteri Destek Ajanısın (AI Agent).
Görevin müşterilere yardımcı olmak, bilgi tabanında arama yapmak ve sipariş işlemlerini gerçekleştirmektir.

YETKİLERİN VE ARAÇLARIN:
1. 'search_knowledge_base': İade, garanti, kargo süresi, SSS ve şirket kuralları hakkında bilgi aramak için kullan.
2. 'get_order_status': Müşteri bir sipariş numarasının kargo/teslimat durumunu sorduğunda kullan.
3. 'cancel_order': Müşteri hazırlanma aşamasındaki bir siparişi iptal etmek istediğinde kullan.
4. 'check_product_stock': Bir ürünün stokta olup olmadığını veya fiyatını kontrol etmek için kullan.

KURALLAR:
- Tahminde bulunma, gerek duyduğun her an ilgili aracı (Tool) çağır.
- Sonuçları her zaman kibar, profesyonel ve çözüm odaklı bir dille müşteriye aktar.
"""

def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Aracı çalıştırır ve konsola görsel bildirim basar."""
    console.print(f"[bold yellow]⚡ [Tool Calling Tetiklendi]:[/bold yellow] [cyan]{tool_name}[/cyan]({json.dumps(arguments, ensure_ascii=False)})")
    result = tool_registry.execute(tool_name, arguments)
    console.print(f"[dim]↳ Araç Çıktısı: {json.dumps(result, ensure_ascii=False)}[/dim]\n")
    return result

def run_agent_turn(user_input: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Kullanıcı mesajını alır, gerekirse Tool çağrılarını icra eder ve nihai cevabı üretir.
    """
    provider = get_active_provider()
    history = history or []

    # 1. OPENAI ENTEGRASYONU
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        
        tools_schema = tool_registry.get_openai_tools_schema()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                tool_result = execute_tool_call(fn_name, fn_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return final_response.choices[0].message.content
        else:
            return msg.content

    # 2. GOOGLE GEMINI ENTEGRASYONU
    elif provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        tool_functions = [t["function"] for t in tool_registry.get_all_tools()]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=tool_functions,
            temperature=0.2
        )
        chat = client.chats.create(model="gemini-2.5-flash", config=config)
        response = chat.send_message(user_input)
        return response.text

    # 3. MOCK / SİMÜLASYON MODU (API Anahtarsız Yerel Akıllı Eşleştirici)
    else:
        text_lower = user_input.lower()
        order_match = re.search(r'#?(\d{5})', user_input)

        # 1. Öncelik: İptal İşlemi
        if ("iptal" in text_lower or "vazgeç" in text_lower) and order_match:
            oid = order_match.group(1)
            result = execute_tool_call("cancel_order", {"order_id": oid})
            if result.get("success"):
                return f"{oid} numaralı siparişiniz başarıyla iptal edilmiş ve ödeme iadesi süreciniz başlatılmıştır."
            else:
                return f"{oid} numaralı siparişiniz iptal edilemedi: {result.get('message')}"

        # 2. Öncelik: Sipariş Durumu Sorgulama
        if order_match or (("kargo" in text_lower or "sipariş" in text_lower) and any(w in text_lower for w in ["nerede", "durumu", "gelir", "takip"])):
            oid = order_match.group(1) if order_match else "10402"
            result = execute_tool_call("get_order_status", {"order_id": oid})
            if result.get("success"):
                detay = result["detaylar"]
                return (
                    f"📦 **{oid} Numaralı Siparişinizin Durumu:**\n"
                    f"- Ürün: {detay['urun']}\n"
                    f"- Durum: **{detay['status']}**\n"
                    f"- Kargo Firması: {detay.get('kargo_firmasi', 'Belirtilmedi')}\n"
                    f"- Tahmini Teslimat: {detay.get('tahmini_teslimat', detay.get('teslim_tarihi', 'Bilinmiyor'))}"
                )
            else:
                return result.get("message", "Sipariş bulunamadı.")

        # 3. Öncelik: Şirket Politikası / İade / Garanti / SSS (Agentic RAG)
        rag_keywords = ["iade", "garanti", "tamir", "politika", "koşul", "taksit", "fatura", "teslimat süresi", "mağaza", "sss"]
        if any(kw in text_lower for kw in rag_keywords):
            result = execute_tool_call("search_knowledge_base", {"query": user_input})
            info = result.get("bulunan_bilgiler", "")
            return (
                f"Şirket politikalarımız ve bilgi tabanımız doğrultusunda:\n\n{info}\n\n"
                "Başka bir konuda yardımcı olabilir miyim?"
            )

        # 4. Öncelik: Stok Kontrolü
        stock_keywords = ["stok", "fiyat", "kaç para", "kaldı mı", "var mı"]
        if any(sk in text_lower for sk in stock_keywords):
            for product in ["klavye", "kulaklık", "mouse"]:
                if product in text_lower:
                    result = execute_tool_call("check_product_stock", {"product_name": product})
                    if result.get("success"):
                        return (
                            f"🔍 **{result['urun'].capitalize()} Stok Bilgisi:**\n"
                            f"- Durum: {result['durum']}\n"
                            f"- Kalan Adet: {result['stok_adedi']}\n"
                            f"- Fiyat: {result['fiyat_tl']} TL"
                        )

        return (
            "Merhaba! Ben TeknoMarket Akıllı Asistanıyım. "
            "Sipariş sorgulama (Örn: #10402 nolu siparişim nerede?), sipariş iptali, "
            "stok kontrolü veya iade/garanti politikalarımız hakkında size yardımcı olabilirim."
        )
