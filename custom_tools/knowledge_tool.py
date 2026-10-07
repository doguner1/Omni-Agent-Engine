"""
knowledge_tool.py - Bilgi Tabanı Arama Aracı (Agentic RAG Tool)
----------------------------------------------------------------
Yapay zeka bu araç sayesinde istediği zaman ChromaDB'de şirket
belgelerini arayabilir (Agentic RAG).
"""

from typing import Dict, Any
from .registry import register_tool
from src.vector_store import query_knowledge_base

@register_tool(
    name="search_knowledge_base",
    description="Şirketin resmi kuralları, iade ve garanti şartları, teslimat süreleri, SSS ve politikaları hakkında bilgi arar.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Bilgi tabanında aranacak arama terimi veya soru (Örn: 'kulaklık iade şartları', 'kargo ücreti')"
            }
        },
        "required": ["query"]
    }
)
def search_knowledge_base(query: str) -> Dict[str, Any]:
    content = query_knowledge_base(query, top_k=2)
    return {
        "success": True,
        "arama_terimi": query,
        "bulunan_bilgiler": content
    }
