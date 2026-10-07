"""
mock_engine.py - Yapay Zeka Simülasyon Motoru (API Anahtarsız Mod)
-----------------------------------------------------------------
Profesyonel yazılım geliştirmede:
Büyük ekiplerde veya CI/CD test süreçlerinde, her test için gerçek LLM API'sine
para harcamamak veya API anahtarı olmayan ortamlarda sistemi geliştirebilmek için
"Mock LLM" (Yapay Zeka Taklitçisi) mimarileri kullanılır.

Bu modül, API anahtarı henüz eklenmemişken de kodların eksiksiz çalışmasını,
akışın (streaming), token mantığının ve prompt davranışlarının gözlemlenmesini sağlar.
Gerçek API anahtarı eklendiğinde sistem otomatik olarak canlı modele geçer!
"""

import time
import json
from typing import Generator, Dict, Any, List

class MockResponse:
    def __init__(self, text: str, prompt_tokens: int = 15, completion_tokens: int = 40):
        self.text = text
        self.content = text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens

    @property
    def usage(self):
        class Usage:
            def __init__(self, p, c, t):
                self.prompt_tokens = p
                self.completion_tokens = c
                self.total_tokens = t
        return Usage(self.prompt_tokens, self.completion_tokens, self.total_tokens)

def simulate_stream(text: str, delay: float = 0.03) -> Generator[str, None, None]:
    """
    Metni gerçek bir LLM gibi kelime kelime/parça parça akıtır.
    """
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)

def get_mock_completion(prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
    """
    Verilen prompt ve system prompt'a göre gerçekçi bir LLM cevabı üretir.
    """
    prompt_lower = prompt.lower()
    system_lower = system_prompt.lower()

    # 1. Aşama 1 - Basit LLM Sorusu (En önemli 3 kavram)
    if "en önemli 3 kavram" in prompt_lower or "yazılımcı" in prompt_lower:
        return (
            "1. Tokenization & Context Window: Modeller kelimeleri token adı verilen matematiksel parçalar olarak işler; bağlam penceresi ise modelin tek seferde hafızasında tutabileceği azami token limitidir.\n\n"
            "2. RAG (Retrieval-Augmented Generation): Modelin halüsinasyon görmesini engellemek için şirketinizin özel dokümanlarından arama yapıp bağlam olarak modele sunma mimarisidir.\n\n"
            "3. Agentic Workflow & Tool Calling: Modelin sadece sohbet etmekle kalmayıp harici API'ları ve veritabanı sorgularını tetikleyerek otonom eylemler gerçekleştirebilmesidir."
        )

    # 2. Aşama 1 - Karakter / Persona Testi
    if "agresif" in system_lower or "ters" in system_lower:
        return "Kodun aynı satırını 100 kere tek tek yazmak yerine döngü kurarsın, iş biter. Daha bunu da bilmiyorsan dökümantasyonu aç da biraz oku!"
    
    if "anaokulu" in system_lower or "5 yaşında" in system_lower:
        return "Döngü tıpkı müzik kutusu veya bir dönme dolap gibidir minik dostum! Şarkı bitene kadar çark tekrar tekrar döner ve sana eğlence sunar!"

    if "kurumsal" in system_lower or "resmi" in system_lower:
        return "Yazılım mühendisliğinde döngü (loop); belirli bir koşul sağlandığı sürece kod bloklarının tekrarlı ve optimize şekilde icra edilmesini sağlayan temel kontrol akış yapısıdır."

    # 3. Aşama 1 - JSON Sentiment Analizi
    if "müşteri yorumu" in system_lower or "json" in system_lower:
        result = {
            "duygu": "Nötr",
            "departman": "Ürün Kalitesi",
            "ozet": "Kargo teslimatı hızlı ve paketleme başarılı bulunurken kumaş kalitesi beğenilmedi."
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    # 4. Genel Sohbet Botu Cevapları
    if "merhaba" in prompt_lower or "selam" in prompt_lower:
        return "Merhaba! TeknoMarket müşteri destek hattına hoş geldiniz. Size bugün ürünlerimiz, kargo durumunuz veya iade süreçleriniz hakkında nasıl yardımcı olabilirim?"
    
    if "kargo" in prompt_lower or "sipariş" in prompt_lower:
        return "Siparişinizi memnuniyetle kontrol edebilirim! Lütfen 5 haneli sipariş numaranızı (Örn: #10402) paylaşabilir misiniz?"

    if "iade" in prompt_lower:
        return "TeknoMarket üzerinden satın aldığınız ürünleri, teslimat tarihinden itibaren 14 gün içerisinde orijinal kutusuyla birlikte ücretsiz olarak iade edebilirsiniz."

    return (
        f"Sorunuzu başarıyla aldım ('{prompt}'). TeknoMarket ekibi olarak sistemlerimizi "
        "kullanıcı memnuniyeti odaklı şekilde sürekli geliştirmekteyiz. Başka nasıl yardımcı olabilirim?"
    )
