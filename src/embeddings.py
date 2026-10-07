"""
embeddings.py - Vektör Gömme (Embedding) Modülü
------------------------------------------------
Kariyer hedefi: "RAG mimarileri, Vektör veritabanları (Chroma, Qdrant vb.)"

Öğreneceğimiz Kavramlar:
1. Embedding Nedir?
   - Metinlerin anlamını ve sözcük dizilimini çok boyutlu bir sayı dizisine (vektör / float listesi)
     çevirme işlemidir.
   - Örn: "kargo teslimat süresi" -> [0.12, -0.45, 0.88, ..., 0.05]

2. Neden Bağımsız Embedding Sınıfı Yazıyoruz?
   - Ağ kesintilerinde veya HuggingFace indirme kısıtlamalarında sistemin çökmesini engeller.
   - Gerçek ortamda Google Gemini/OpenAI embedding API'leri kullanılır;
     yerel testlerde ise 100% bağımsız, çevrimdışı semantik vektörleştirici çalışır.
"""

import re
import math
import hashlib
from typing import List, Union
import numpy as np

# Windows UTF-8 desteği
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

class RobustSemanticEmbedding:
    """
    ChromaDB ile %100 uyumlu, harici internet indirmesi gerektirmeyen,
    anlamsal yakınlığı ve anahtar kelime örtüşmelerini ölçen yerel vektörleştirici.
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def name(self) -> str:
        return "robust_semantic_embedding"

    def _text_to_vector(self, text: str) -> List[float]:
        text_clean = text.lower()
        words = re.findall(r'\b\w+\b', text_clean)
        
        vec = np.zeros(self.dimension, dtype=np.float32)
        if not words:
            return vec.tolist()

        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        for token in tokens:
            h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def __call__(self, input: Union[List[str], str]) -> List[List[float]]:
        if isinstance(input, str):
            input = [input]
        return [self._text_to_vector(t) for t in input]

    def embed_query(self, input: Union[List[str], str]) -> List[List[float]]:
        return self(input)

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self(input)

def get_embedding_function():
    return RobustSemanticEmbedding(dimension=128)
