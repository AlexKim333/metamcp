import os
import sys
import json
import re
import datetime
import requests
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
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
    clean = query.strip()
    if not clean:
        return []
    
    variations = [clean]
    m = re.match(r'^([A-Za-z]+)(\d+.*)$', clean)
    if m:
        hyphenated = f"{m.group(1)}-{m.group(2)}"
        if hyphenated not in variations:
            variations.append(hyphenated)
            
    dehyphenated = clean.replace("-", "").replace(" ", "")
    if dehyphenated not in variations:
        variations.append(dehyphenated)
        
    digits = re.findall(r'\d+', clean)
    if digits:
        for d in digits:
            if len(d) >= 3 and d not in variations:
                variations.append(d)
                
    return variations

def search_items(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """ERPNext에서 품목(Item)을 검색합니다."""
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
                if len(results) >= 5:
                    break
        except Exception as e:
            print(f"❌ 품목 검색 오류 ({term}): {e}")

    return results[:limit]

def get_item_stock(item_code: str, warehouse: Optional[str] = None) -> Dict[str, object]:
    """특정 품목(item_code)의 실시간 지점별 재고(Bin) 수량을 조회합니다."""
    clean_code = item_code.strip()
    headers = _get_headers()

    item_info = {}
    try:
        item_res = requests.get(f"{ERPNEXT_URL}/api/resource/Item/{requests.utils.quote(clean_code)}", headers=headers, timeout=10)
        if item_res.status_code == 200:
            item_info = item_res.json().get("data", {})
    except Exception:
        pass

    pack_qty = int(item_info.get("custom_pack_qty") or 1)

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
            return {"success": False, "error": f"ERPNext 응답 실패: {bin_res.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_warehouses() -> List[Dict[str, str]]:
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

def get_item_price(item_code: str) -> Dict[str, object]:
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

def get_recent_stock_transfers(limit: int = 5) -> List[Dict[str, object]]:
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

def _ensure_customer_exists(customer_name: str, customer_phone: str = "") -> str:
    headers = _get_headers()
    clean_name = customer_name.strip()
    if not clean_name:
        clean_name = "Walk-in Customer"

    try:
        check_res = requests.get(f"{ERPNEXT_URL}/api/resource/Customer/{requests.utils.quote(clean_name)}", headers=headers, timeout=10)
        if check_res.status_code == 200:
            return clean_name
    except Exception:
        pass

    try:
        payload = {
            "customer_name": clean_name,
            "customer_type": "Individual",
            "customer_group": "Commercial",
            "territory": "All Territories"
        }
        if customer_phone:
            payload["mobile_no"] = customer_phone
            
        create_res = requests.post(f"{ERPNEXT_URL}/api/resource/Customer", headers=headers, json=payload, timeout=10)
        if create_res.status_code in [200, 201]:
            data = create_res.json().get("data", {})
            return data.get("name") or clean_name
    except Exception as e:
        print(f"고객 생성 예외: {e}")

    return clean_name

class OrderItemInput(BaseModel):
    item_code: str = Field(description="품목 코드 (예: 'P-160-ROJO-400')")
    boxes: float = Field(default=0.0, description="박스 수량 (예: 2박스이면 2.0)")
    qty: float = Field(default=0.0, description="낱개 수량 (박스 수량이 없을 때)")
    rate_per_box: float = Field(default=0.0, description="박스당 단가 (예: 300.0)")
    rate: float = Field(default=0.0, description="낱개당 단가")

def create_sales_order(
    customer_name: str,
    items_list: List[OrderItemInput],
    warehouse: Optional[str] = None,
    customer_phone: str = "",
    notes: str = ""
) -> Dict[str, object]:
    """
    [ERPNext 판매 주문서(Sales Order) 자동 등록 도구]
    :param customer_name: 고객명 (예: 'Carlos Gomez')
    :param items_list: 주문할 품목 리스트
    :param warehouse: 출고 지점 (예: 'IKEA', '[MAIN] ALARCON - K')
    :param customer_phone: 고객 WhatsApp 전화번호
    :param notes: 특이사항 메모
    """
    headers = _get_headers()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    customer_code = _ensure_customer_exists(customer_name, customer_phone)

    wh_target = "[MAIN] ALARCON - K"
    if warehouse:
        all_wh = get_warehouses()
        for w in all_wh:
            w_name = w.get("name", "")
            if warehouse.lower() in w_name.lower():
                wh_target = w_name
                break

    so_items = []
    total_order_amount = 0.0
    parsed_summary = []

    for it in items_list:
        # dict 또는 BaseModel 모두 호환 처리
        if isinstance(it, dict):
            code = it.get("item_code", "").strip()
            boxes = float(it.get("boxes") or 0)
            eaches = float(it.get("qty") or 0)
            rate_per_box = float(it.get("rate_per_box") or 0)
            unit_rate = float(it.get("rate") or 0)
        else:
            code = it.item_code.strip()
            boxes = float(it.boxes or 0)
            eaches = float(it.qty or 0)
            rate_per_box = float(it.rate_per_box or 0)
            unit_rate = float(it.rate or 0)

        st = get_item_stock(code)
        pack_qty = int(st.get("pack_qty") or 1)
        item_name = str(st.get("item_name") or code)

        if boxes > 0:
            final_qty = boxes * pack_qty
            line_amount = (boxes * rate_per_box) if rate_per_box > 0 else (final_qty * unit_rate)
            final_unit_rate = (line_amount / final_qty) if final_qty > 0 else unit_rate
        else:
            final_qty = eaches if eaches > 0 else 1
            line_amount = final_qty * unit_rate
            final_unit_rate = unit_rate
            boxes = int(final_qty // pack_qty)

        total_order_amount += line_amount

        so_items.append({
            "item_code": code,
            "item_name": item_name,
            "qty": final_qty,
            "rate": round(final_unit_rate, 4),
            "amount": round(line_amount, 2),
            "warehouse": wh_target,
            "delivery_date": today_str
        })

        parsed_summary.append({
            "item_code": code,
            "boxes": boxes,
            "pack_qty": pack_qty,
            "total_qty": int(final_qty),
            "rate_per_box": rate_per_box,
            "line_amount": round(line_amount, 2)
        })

    order_payload = {
        "naming_series": "SO-.YYYY.-",
        "customer": customer_code,
        "company": "kecon",
        "transaction_date": today_str,
        "delivery_date": today_str,
        "set_warehouse": wh_target,
        "items": so_items,
        "remarks": notes or f"WhatsApp 삼돌이 AI 자동 생성 (고객: {customer_name}, 전화: {customer_phone})"
    }

    try:
        url = f"{ERPNEXT_URL}/api/resource/Sales Order"
        res = requests.post(url, headers=headers, json=order_payload, timeout=15)
        
        if res.status_code in [200, 201]:
            created_data = res.json().get("data", {})
            order_name = created_data.get("name")
            return {
                "success": True,
                "order_name": order_name,
                "customer": customer_code,
                "customer_phone": customer_phone,
                "warehouse": wh_target,
                "total_amount": round(total_order_amount, 2),
                "items": parsed_summary
            }
        else:
            return {
                "success": False,
                "error": f"ERPNext 오류 ({res.status_code}): {res.text}",
                "simulated_summary": {
                    "customer": customer_code,
                    "total_amount": total_order_amount,
                    "items": parsed_summary
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "simulated_summary": {
                "customer": customer_code,
                "total_amount": total_order_amount,
                "items": parsed_summary
            }
        }
