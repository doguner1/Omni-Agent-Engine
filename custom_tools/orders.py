"""
orders.py - Sipariş ve E-Ticaret Araçları (Örnek API Entegrasyonları)
---------------------------------------------------------------------
Bu dosya şirketin veritabanı veya harici kargo/stok API'larını simüle eder.
Gerçek projelerde burada 'requests.get("https://api.kargo.com/...")'
veya SQL sorguları çalışır.
"""

from typing import Dict, Any
from .registry import register_tool

# Sahte Şirket Veritabanı
MOCK_DATABASE = {
    "orders": {
        "10402": {
            "status": "Kargoda",
            "kargo_firmasi": "Aras Kargo",
            "takip_no": "TR-994821",
            "urun": "Kablosuz Bluetooth Kulaklık",
            "tahmini_teslimat": "Yarın saat 14:00'e kadar",
            "tutar": 1299.00
        },
        "10403": {
            "status": "Hazırlanıyor",
            "urun": "Mekanik Klavye (RGB)",
            "kargo_firmasi": "Henüz atanmadı",
            "tahmini_teslimat": "2 iş günü içinde",
            "tutar": 2450.00
        },
        "10404": {
            "status": "Teslim Edildi",
            "urun": "Akıllı Saat",
            "kargo_firmasi": "Yurtiçi Kargo",
            "teslim_tarihi": "06.10.2026 15:30",
            "tutar": 3800.00
        }
    },
    "stock": {
        "klavye": {"stok": 14, "fiyat": 2450.00, "reyon": "A-12"},
        "kulaklık": {"stok": 0, "fiyat": 1299.00, "reyon": "B-04"},
        "mouse": {"stok": 58, "fiyat": 750.00, "reyon": "A-08"}
    }
}

@register_tool(
    name="get_order_status",
    description="Kullanıcının verdiği sipariş numarasına göre kargo ve teslimat durumunu sorgular.",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "5 haneli sipariş takip numarası (Örn: '10402')"
            }
        },
        "required": ["order_id"]
    }
)
def get_order_status(order_id: str) -> Dict[str, Any]:
    order_id = str(order_id).strip().replace("#", "")
    order = MOCK_DATABASE["orders"].get(order_id)
    if not order:
        return {
            "success": False,
            "message": f"'{order_id}' numaralı bir sipariş sistemimizde bulunamadı. Lütfen numarayı kontrol ediniz."
        }
    return {
        "success": True,
        "order_id": order_id,
        "detaylar": order
    }

@register_tool(
    name="cancel_order",
    description="Hazırlık aşamasındaki bir siparişi iptal eder. Kargoya verilmiş veya teslim edilmiş siparişler iptal edilemez.",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "İptal edilmek istenen sipariş numarası (Örn: '10403')"
            }
        },
        "required": ["order_id"]
    }
)
def cancel_order(order_id: str) -> Dict[str, Any]:
    order_id = str(order_id).strip().replace("#", "")
    order = MOCK_DATABASE["orders"].get(order_id)
    if not order:
        return {"success": False, "message": f"Sipariş bulunamadı: {order_id}"}
        
    if order["status"] == "Hazırlanıyor":
        order["status"] = "İptal Edildi"
        return {
            "success": True,
            "message": f"{order_id} numaralı sipariş başarıyla iptal edildi. Para iadesi bankanıza iletildi."
        }
    else:
        return {
            "success": False,
            "message": f"Sipariş iptal edilemez! Sipariş durumu şu anda '{order['status']}'. Yalnızca 'Hazırlanıyor' aşamasındaki siparişler iptal edilebilir."
        }

@register_tool(
    name="check_product_stock",
    description="Depodaki ürünün stok adedini ve güncel satış fiyatını sorgular.",
    parameters={
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Aranacak ürünün adı (Örn: 'klavye', 'kulaklık', 'mouse')"
            }
        },
        "required": ["product_name"]
    }
)
def check_product_stock(product_name: str) -> Dict[str, Any]:
    key = product_name.lower().strip()
    for name, data in MOCK_DATABASE["stock"].items():
        if name in key or key in name:
            return {
                "success": True,
                "urun": name,
                "stok_adedi": data["stok"],
                "fiyat_tl": data["fiyat"],
                "durum": "Stokta Var" if data["stok"] > 0 else "Tükendi"
            }
    return {"success": False, "message": f"'{product_name}' isimli ürün stok sisteminde bulunamadı."}
