import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import google.genai as genai

from django_app.domain.stock_event import (
    StockEvent,
    VALID_EVENT_TYPES,
    VALID_PRIORITIES,
    validate_stock_event_data,
)
from django_app.repository.stock_event_repository import StockEventRepository

_repository: Optional[StockEventRepository] = None


def set_repository(repo: StockEventRepository):
    global _repository
    _repository = repo


def create(data: dict) -> Tuple[Optional[StockEvent], dict]:
    is_valid, errors = validate_stock_event_data(data)
    if not is_valid:
        return None, errors
    
    event_type = data.get("event_type", "")
    products = data.get("products", [])
    
    outgoing_types = ["Delivery", "Sale", "Expiry"]
    incoming_types = ["Restock", "Return", "Reorder"]
    
    from django_app.domain import product_service
    all_products, _ = product_service.list_products(1, 1000)
    product_map = {p.name: p for p in all_products}
    
    for product_entry in products:
        product_name = product_entry.get("product_name", "")
        quantity_change = product_entry.get("quantity_change", 0)
        
        if quantity_change == 0:
            continue
            
        product = product_map.get(product_name)
        
        if event_type in outgoing_types:
            if quantity_change > 0:
                return None, {"quantity": f"{event_type} events must have negative quantities (removing stock)"}
            if product and abs(quantity_change) > product.quantity:
                return None, {"quantity": f"Cannot {event_type.lower()} {abs(quantity_change)} units of '{product_name}' — only {product.quantity} available"}
        
        if event_type in incoming_types:
            if quantity_change < 0:
                return None, {"quantity": f"{event_type} events must have positive quantities (adding stock)"}
        
        if event_type == "Audit":
            if quantity_change < 0 and product and abs(quantity_change) > product.quantity:
                return None, {"quantity": f"Cannot remove {abs(quantity_change)} units of '{product_name}' via audit — only {product.quantity} available"}
    
    return _repository.create(data), {}


def get_by_id(event_id: str) -> Optional[StockEvent]:
    return _repository.get_by_id(event_id)


def list_events(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    event_type: Optional[str] = None,
) -> Tuple[List[StockEvent], int]:
    return _repository.list_events(page, page_size, status, priority, event_type)


def update(event_id: str, data: dict) -> Tuple[Optional[StockEvent], dict]:
    is_valid, errors = validate_stock_event_data(data, for_update=True)
    if not is_valid:
        return None, errors
    return _repository.update(event_id, data), {}


def delete(event_id: str) -> bool:
    return _repository.delete(event_id)


def get_upcoming_events(days: int = 30) -> List[StockEvent]:
    return _repository.get_upcoming_events(days)


def get_event_summary() -> dict:
    all_events, _ = _repository.list_events(1, 1000)
    
    pending = [e for e in all_events if e.status == "pending"]
    completed = [e for e in all_events if e.status == "completed"]
    
    by_priority = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for e in all_events:
        if e.priority in by_priority:
            by_priority[e.priority] += 1
    
    by_type = {t: 0 for t in VALID_EVENT_TYPES}
    for e in all_events:
        if e.event_type in by_type:
            by_type[e.event_type] += 1
    
    return {
        "total": len(all_events),
        "pending": len(pending),
        "completed": len(completed),
        "cancelled": len(all_events) - len(pending) - len(completed),
        "by_priority": by_priority,
        "by_type": by_type,
        "upcoming_7_days": len([e for e in pending if _is_within_days(e.expected_date, 7)]),
        "upcoming_30_days": len([e for e in pending if _is_within_days(e.expected_date, 30)]),
    }


def _is_within_days(date_str: str, days: int) -> bool:
    try:
        date = datetime.strptime(date_str, "%b %d, %Y")
        today = datetime.now()
        future = today + timedelta(days=days)
        return today <= date <= future
    except ValueError:
        return False


def generate_ai_event(
    user_prompt: str,
    product_list: list,  # list of dicts: {name, quantity, price, brand, category}
) -> Tuple[Optional[dict], str]:
    """
    Given a free-text prompt and the current product inventory, use AI to produce
    ONE event object: { event_name, event_type, priority, expected_date, description,
                        products: [{product_name, quantity_change}, ...] }
    Returns (event_dict, error_message). On failure returns (None, error_message).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY is not configured on the server."

    client = genai.Client(api_key=api_key)

    today = datetime.now()
    default_date = (today + timedelta(days=7)).strftime("%b %d, %Y")

    product_lines = "\n".join(
        f"- {p['name']} | Stock: {p.get('quantity', 0)} | Price: ₹{p.get('price', 0)} | Brand: {p.get('brand', 'N/A')} | Category: {p.get('category', 'N/A')}"
        for p in product_list
    )

    prompt = f"""You are an inventory management assistant. A user wants to create a stock event.

USER REQUEST: "{user_prompt}"

AVAILABLE PRODUCTS IN INVENTORY:
{product_lines}

TASK: Based on the user's request, select the most relevant products from the inventory above and create ONE stock event that covers all of them. Each product can have its own quantity change.

Rules:
- Only use product names that EXACTLY match names from the inventory list above.
- quantity_change must be a non-zero integer (positive = stock coming in, negative = stock going out).
- event_type must be one of: Delivery, Restock, Sale, Return, Audit, Expiry, Reorder
- priority must be one of: Low, Medium, High, Critical
- expected_date must be in format "MMM DD, YYYY" (e.g. "{default_date}")
- Pick a meaningful event_name (3-6 words) summarising the user's intent.
- Select 1-8 of the most relevant products. Do not include products that are irrelevant to the request.
- Use sensible quantities based on current stock levels and the nature of the event.

Return ONLY a valid JSON object with NO markdown, NO backticks, NO explanation:
{{
  "event_name": "string",
  "event_type": "string",
  "priority": "string",
  "expected_date": "string",
  "description": "string (one sentence)",
  "products": [
    {{"product_name": "exact name from inventory", "quantity_change": integer}},
    ...
  ]
}}"""

    try:
        from google.genai import types as genai_types
        config = genai_types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=1024,
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        event_dict = json.loads(raw)

        required = ["event_name", "event_type", "priority", "expected_date", "products"]
        for key in required:
            if key not in event_dict:
                return None, f"AI response missing required field: '{key}'"

        if event_dict["event_type"] not in VALID_EVENT_TYPES:
            return None, f"AI returned invalid event_type: '{event_dict['event_type']}'. Must be one of {VALID_EVENT_TYPES}."

        if event_dict["priority"] not in VALID_PRIORITIES:
            return None, f"AI returned invalid priority: '{event_dict['priority']}'. Must be one of {VALID_PRIORITIES}."

        if not isinstance(event_dict["products"], list) or len(event_dict["products"]) == 0:
            return None, "AI did not select any products. Try a more specific prompt."

        valid_names = {p["name"] for p in product_list}
        cleaned_products = []
        for item in event_dict["products"]:
            pname = item.get("product_name", "")
            qty = item.get("quantity_change")
            if pname not in valid_names:
                continue  
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 0
            if qty == 0:
                continue
            cleaned_products.append({"product_name": pname, "quantity_change": qty})

        if not cleaned_products:
            return None, "AI could not match any products from your inventory to this request. Try rephrasing."

        event_dict["products"] = cleaned_products
        return event_dict, ""

    except json.JSONDecodeError as e:
        return None, f"AI returned malformed JSON: {e}. Raw response: {raw[:200]}"
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return None, f"AI generation error: {str(e)}"


def apply_event_to_inventory(event_id: str) -> Tuple[bool, str]:
    from django_app.domain import product_service
    import logging
    logger = logging.getLogger(__name__)
    
    event = get_by_id(event_id)
    if not event:
        return False, "Event not found"
    
    if event.status == "completed":
        return False, "Event already applied"
    
    logger.info(f"Applying event {event_id}: {event.event_name}, products: {event.products}")
    
    if event.products and len(event.products) > 0:
        applied_products = []
        failed_products = []
        
        for idx, product_entry in enumerate(event.products):
            product_name = product_entry.get("product_name", "")
            quantity_change = product_entry.get("quantity_change", 0)
            product_id = product_entry.get("product_id")
            
            logger.info(f"Processing product {idx}: name={product_name}, id={product_id}, qty_change={quantity_change}")
            
            product = None
            if product_id:
                product = product_service.get_by_id(product_id)
                logger.info(f"Looked up by ID {product_id}: found={product is not None}")
            
            if not product:
                products, _ = product_service.list_products(1, 100)
                for p in products:
                    if p.name.lower() == product_name.lower():
                        product = p
                        break
                logger.info(f"Looked up by name '{product_name}': found={product is not None}")
            
            if not product:
                failed_products.append(f"{product_name} (not found)")
                logger.warning(f"Product not found: {product_name}")
                continue
            
            logger.info(f"Current quantity for {product.name}: {product.quantity}, change: {quantity_change}")
            new_quantity = product.quantity + quantity_change
            if new_quantity < 0:
                failed_products.append(f"{product_name} (insufficient stock)")
                logger.warning(f"Insufficient stock for {product_name}")
                continue
            
            result = product_service.update(product.id, {"quantity": new_quantity})
            logger.info(f"Updated {product.name} (ID: {product.id}): {product.quantity} -> {new_quantity}, result={result}")
            applied_products.append(f"{product.name}: {quantity_change:+d}")
        
        if not applied_products:
            return False, f"No products could be applied. Failures: {', '.join(failed_products)}"
        
        update(event_id, {"status": "completed"})
        
        result_msg = f"Applied {event.event_type} to {len(applied_products)} product(s)"
        if failed_products:
            result_msg += f". Skipped: {', '.join(failed_products)}"
        logger.info(f"Event {event_id} applied: {result_msg}")
        return True, result_msg
    
    return False, "No products in this event"