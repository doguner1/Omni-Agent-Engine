"""
registry.py - Tak-Çalıştır Araç (Tool) Yönetim Sistemi
------------------------------------------------------
Kariyer hedefi: "AI Agent, tool calling, function calling ve API entegrasyonları"

Bu modül, projeye yeni bir API veya fonksiyon eklemeyi son derece kolaylaştırır.
Herhangi bir Python fonksiyonunun üzerine '@register_tool' eklediğinizde:
1. Otomatik olarak OpenAI ve Gemini modellerinin anlayacağı JSON şemasına dönüştürülür.
2. Model bu aracı çağırmak istediğinde güvenli bir şekilde çalıştırılır ve sonucu modele iletilir.
"""

import inspect
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        """Yeni bir fonksiyonu araç olarak kaydetmek için dekoratör."""
        def decorator(func: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "function": func
            }
            return func
        return decorator

    def get_tool(self, name: str) -> Dict[str, Any]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Modele gelen tool çağrısını güvenli bir şekilde çalıştırır."""
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"'{name}' isimli araç bulunamadı."}
        try:
            func = tool["function"]
            return func(**arguments)
        except Exception as e:
            return {"error": f"Araç çalıştırma hatası: {str(e)}"}

    def get_openai_tools_schema(self) -> List[Dict[str, Any]]:
        """OpenAI Function Calling formatına dönüştürür."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return schemas

# Global Tekil Kayıt Defteri (Singleton Registry)
tool_registry = ToolRegistry()
register_tool = tool_registry.register
