import os
import sys
import json
import re
import requests
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

ERPNEXT_URL = os.getenv("ERPNEXT_URL", "https://ktkpos.frappe.cloud").rstrip("/")
API_KEY = os.getenv("ERPNEXT_API_KEY")
API_SECRET = os.getenv("ERPNEXT_API_SECRET")

def _get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def _generate_search_variations(query: str) -> List[str]:
    """
    품목 검색어 유연화 (P160 -> ['P160', 'P-160', '160', 'PL160', 'L-PL160'])
    하이픈 누락이나 서브코드 불일치를 완벽히 방어
    """
    clean = query.strip()
    if not clean:
        return []
    
    variations = [clean]
    
    # 1. 영문+숫자 결합형 (P160 -> P-160)
    m = re.match(r'^([A-Za-z]+)(\d+.*)$', clean)
    if m:
        hyphenated = f"{m.group(1)}-{m.group(2)}"
        if hyphenated not in variations:
            variations.append(hyphenated)
            
    # 2. 하이픈 제거형 (P-160 -> P160)
    dehyphenated = clean.replace("-", "").replace(" ", "")
    if dehyphenated not in variations:
        variations.append(dehyphenated)
        
    # 3. 숫자 부분만 추출 (P160 -> 160)
    digits = re.findall(r'\d+', clean)
    if digits:
        for d in digits:
            if len(d) >= 3 and d not in variations:
                variations.append(d)
                
    return variations

def search_items(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ERPNext에서 품목(Item)을 검색합니다. (P160, P-160 등 하이픈 누락 자동 보정)
    :param query: 검색할 품목코드 또는 품명 (예: 'P160', '021G', 'P-D60')
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    url = f"{ERPNEXT_URL}/api/resource/Item"
    headers = _get_headers()
    fields = json.dumps(["name", "item_name", "item_group", "stock_uom", "custom_pack_qty", "disabled"])
    
    search_terms = _generate_search_variations(clean_q)
    
    seen_names = set()
    results = []

    for term in search_terms:
        params = {
            "fields": fields,
            "filters": json.dumps([["disabled", "=", 0]]),
            "or_filters": json.dumps([
                ["name", "like", f"%{term}%"],
                ["item_name", "like", f"%{term}%"]
            ]),
            "limit_page_length": limit,
            "order_by": "modified desc"
        }

        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                items = res.json().get("data", [])
                for item in items:
                    iname = item.get("name")
                    if iname not in seen_names:
                        seen_names.add(iname)
                        results.append(item)
                # 이미 충분한 결과를 얻었으면 추가 변형 검색 중단
                if len(results) >= 5:
                    break
        except Exception as e:
            print(f"❌ 품목 검색 오류 ({term}): {e}")

    return results[:limit]

def get_item_stock(item_code: str, warehouse: Optional[str] = None) -> Dict[str, Any]:
    """
    특정 품목(item_code)의 실시간 지점별 재고(Bin) 수량을 조회합니다.
    """
    clean_code = item_code.strip()
    headers = _get_headers()

    # 1. Item 마스터 정보 조회
    item_info = {}
    try:
        item_res = requests.get(f"{ERPNEXT_URL}/api/resource/Item/{requests.utils.quote(clean_code)}", headers=headers, timeout=10)
        if item_res.status_code == 200:
            item_info = item_res.json().get("data", {})
    except Exception:
        pass

    pack_qty = int(item_info.get("custom_pack_qty") or 1)

    # 2. Bin 재고 목록 조회
    filters = [["item_code", "=", clean_code]]
    if warehouse:
        filters.append(["warehouse", "like", f"%{warehouse.strip()}%"])

    params = {
        "fields": json.dumps(["name", "warehouse", "actual_qty", "projected_qty", "reserved_qty"]),
        "filters": json.dumps(filters),
        "limit_page_length": 50
    }

    try:
        bin_res = requests.get(f"{ERPNEXT_URL}/api/resource/Bin", headers=headers, params=params, timeout=10)
        if bin_res.status_code == 200:
            bins = bin_res.json().get("data", [])
            
            stock_by_wh = []
            total_actual_qty = 0
            
            for b in bins:
                qty = float(b.get("actual_qty", 0))
                boxes = int(qty // pack_qty) if pack_qty > 0 else int(qty)
                eaches = int(qty % pack_qty) if pack_qty > 0 else 0
                
                stock_by_wh.append({
                    "warehouse": b.get("warehouse"),
                    "actual_qty": qty,
                    "boxes": boxes,
                    "eaches": eaches,
                    "projected_qty": float(b.get("projected_qty", 0))
                })
                total_actual_qty += qty

            return {
                "success": True,
                "item_code": clean_code,
                "item_name": item_info.get("item_name", clean_code),
                "pack_qty": pack_qty,
                "stock_uom": item_info.get("stock_uom", "Nos"),
                "total_qty": total_actual_qty,
                "total_boxes": int(total_actual_qty // pack_qty) if pack_qty > 0 else int(total_actual_qty),
                "total_eaches": int(total_actual_qty % pack_qty) if pack_qty > 0 else 0,
                "warehouses": stock_by_wh
            }
        else:
            return {
                "success": False,
                "error": f"ERPNext 응답 실패 (HTTP {bin_res.status_code}): {bin_res.text}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_warehouses() -> List[Dict[str, Any]]:
    """ERPNext의 모든 활성 창고(Warehouse) 목록을 조회합니다."""
    headers = _get_headers()
    params = {
        "fields": json.dumps(["name", "warehouse_name", "company"]),
        "filters": json.dumps([["disabled", "=", 0], ["is_group", "=", 0]]),
        "limit_page_length": 50
    }
    try:
        res = requests.get(f"{ERPNEXT_URL}/api/resource/Warehouse", headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
        return []
    except Exception as e:
        print(f"❌ 창고 목록 조회 오류: {e}")
        return []

def get_item_price(item_code: str) -> Dict[str, Any]:
    """특정 품목의 판매 단가를 조회합니다."""
    clean_code = item_code.strip()
    headers = _get_headers()
    params = {
        "fields": json.dumps(["name", "price_list", "price_list_rate", "custom_tier_2_price", "custom_tier_3_price", "custom_tier_4_price"]),
        "filters": json.dumps([["item_code", "=", clean_code]]),
        "limit_page_length": 10
    }
    try:
        res = requests.get(f"{ERPNEXT_URL}/api/resource/Item Price", headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            prices = res.json().get("data", [])
            return {"success": True, "item_code": clean_code, "prices": prices}
        return {"success": False, "error": res.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_recent_stock_transfers(limit: int = 5) -> List[Dict[str, Any]]:
    """최근 생성된 지점 이동 전표(Stock Entry - Material Transfer) 목록을 조회합니다."""
    headers = _get_headers()
    params = {
        "fields": json.dumps(["name", "posting_date", "posting_time", "stock_entry_type", "docstatus", "from_warehouse", "to_warehouse", "total_outgoing_value"]),
        "filters": json.dumps([["stock_entry_type", "=", "Material Transfer"]]),
        "order_by": "creation desc",
        "limit_page_length": limit
    }
    try:
        res = requests.get(f"{ERPNEXT_URL}/api/resource/Stock Entry", headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
        return []
    except Exception as e:
        print(f"❌ 최근 전표 조회 오류: {e}")
        return []

