from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from pydantic import BaseModel, Field
try:
    from django_app.domain.product_service import get_by_id, list_products
except ImportError:
    def get_by_id(product_id): raise Exception("Django not available")
    def list_products(**kwargs): raise Exception("Django not available")

try:
    from django_app.domain.rag_service import build_rag_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

DISCOUNT_TIERS = [(100, 0.20), (50, 0.10), (20, 0.05), (0, 0.00)]
MAX_DISCOUNT   = 0.20

SYSTEM_PROMPT = """\
You are an intelligent inventory assistant. Each message you receive contains pre-fetched context sections followed by the user's request. Use the context before reaching for tools.

Context sections injected into every message:
- INVENTORY DATA     — live snapshot: totals, rankings, low-stock alerts, all categories and brands.
- PRODUCT CONTEXT    — semantic chunks for products relevant to this query.
- POLICY & DOCS      — warranties, return windows, refund rules, FAQs.
- CONVERSATION HISTORY — recent turns for continuity.

When to answer directly from context (no tool call needed):
- General inventory questions, rankings, overviews → use INVENTORY DATA.
- Policy, warranty, return questions               → use POLICY & DOCS.
- Product descriptions already in PRODUCT CONTEXT → use them directly.

When to use tools:
- search_products   → product mentioned by name but not found in PRODUCT CONTEXT.
- get_product_info  → need full details and already have an ID.
- check_inventory   → user explicitly asks about current stock level.
- calculate_quote   → quantity + price calculation required for a single product.
- compare_products  → comparing multiple products (provide IDs).
- multi_item_quote  → basket order with multiple products + quantities in one call.

Rules:
- Never say "I cannot access pricing" — use search_products immediately.
- For comparisons: search_products for IDs first, then compare_products with all IDs at once.
- For basket orders: use multi_item_quote in a single call.
- Format all prices as ₹X.XX.
- Be concise: lead with the answer, follow with detail."""


def _resolve_discount(quantity: int) -> tuple[float, str]:
    for min_qty, rate in DISCOUNT_TIERS:
        if quantity >= min_qty:
            label = f"{int(rate*100)}% off for ≥{min_qty} units" if rate else "No discount"
            return min(rate, MAX_DISCOUNT), label
    return 0.0, "No discount"


def _get_trigrams(text: str) -> List[str]:
    text = text.lower()
    trigrams = []
    for i in range(len(text) - 2):
        trigrams.append(text[i:i+3])
    return trigrams

def _fuzzy_match(query: str, text: str) -> bool:
    query_lower = query.lower()
    text_lower = text.lower()
    if query_lower in text_lower:
        return True
    q_words = query_lower.split()
    if all(word in text_lower for word in q_words):
        return True
    query_trigrams = _get_trigrams(query_lower)
    text_trigrams = _get_trigrams(text_lower)
    
    if query_trigrams and text_trigrams:
        common_trigrams = set(query_trigrams) & set(text_trigrams)
        trigram_similarity = len(common_trigrams) / len(set(query_trigrams) if query_trigrams else 0)
        if trigram_similarity >= 0.3:
            return True    
    return False


def _extract_response_text(result: dict) -> str:
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", str(last))
    if isinstance(content, list):
        return " ".join(
            x.get("text", str(x)) if isinstance(x, dict) else str(x)
            for x in content
        )
    return str(content)


def _extract_tool_calls(result: dict) -> list:
    calls = []
    for msg in result.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                calls.append({"tool": tc.get("name", "unknown"), "args": tc.get("args", {})})
    return calls


def _extract_quote(result: dict) -> Optional[dict]:
    for msg in result.get("messages", []):
        if getattr(msg, "name", None) == "calculate_quote":
            try:
                content = msg.content
                parsed  = json.loads(content) if isinstance(content, str) else content
                if isinstance(parsed, dict) and "total" in parsed:
                    return parsed
            except Exception:
                pass
    return None



class CompareProductsInput(BaseModel):
    product_ids: List[str] = Field(description="List of product IDs to compare")

class QuoteItem(BaseModel):
    product_id: str = Field(description="Product ID")
    quantity: int   = Field(description="Quantity to quote")

class MultiItemQuoteInput(BaseModel):
    items: List[QuoteItem] = Field(description="List of products and quantities")

class QuoteAgentService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.llm     = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=self.api_key,
            temperature=0.1,
        )
        self.tools = self._build_tools()
        self.agent = create_react_agent(self.llm, self.tools, prompt=SYSTEM_PROMPT)

    def _build_tools(self):

        @tool
        def search_products(query: str) -> list:
            """
            Search the LOCAL product database by name, brand, category, or description.
            Supports partial and multi-word queries (e.g. 'esp8266', 'lipo battery', 'node mcu').
            Returns matching products with their IDs — always call this first when you have a
            product name but no ID.
            """
            try:
                products, _ = list_products(page=1, page_size=200)
                q = query.strip()
                results = []
                for p in products:
                    searchable = f"{p.name} {p.brand} {p.category} {getattr(p,'description','')}"
                    if _fuzzy_match(q, searchable):
                        results.append({
                            "id":                 str(p.id),
                            "name":               p.name,
                            "brand":              p.brand,
                            "category":           p.category,
                            "unit_price":         float(p.price),
                            "quantity_available": int(p.quantity),
                        })
                return results[:5]
            except Exception as e:
                return [{"error": f"Search failed: {e}"}]

        @tool
        def get_product_info(product_id: str) -> dict:
            """
            Retrieve full product details by exact product ID.
            Returns name, brand, category, unit price, stock, and description.
            Use search_products first if you only have a name.
            """
            try:
                p = get_by_id(product_id)
                if p is None:
                    return {"error": f"Product not found: {product_id}"}
                return {
                    "id":                 str(p.id),
                    "name":               p.name,
                    "brand":              p.brand,
                    "category":           p.category,
                    "unit_price":         float(p.price),
                    "quantity_available": int(p.quantity),
                    "description":        getattr(p, "description", ""),
                }
            except Exception as e:
                return {"error": f"Product lookup failed: {e}"}

        @tool
        def check_inventory(product_id: str) -> dict:
            """
            Check current stock level for a product by ID.
            Returns quantity, in_stock flag, status (Available / Low stock / Out of stock),
            and whether a reorder is suggested.
            """
            try:
                p   = get_by_id(product_id)
                if p is None:
                    return {"error": f"Product not found: {product_id}"}
                qty = int(p.quantity)
                return {
                    "product_id":         product_id,
                    "product_name":       p.name,
                    "quantity_available": qty,
                    "in_stock":           qty > 0,
                    "status":             "Available" if qty > 5 else ("Low stock" if qty > 0 else "Out of stock"),
                    "reorder_suggested":  qty <= 5,
                }
            except Exception as e:
                return {"error": f"Inventory check failed: {e}"}

        @tool
        def calculate_quote(product_id: str, quantity: int) -> dict:
            """
            Calculate a price quote with volume discounts.
            Discount tiers (enforced, cannot be overridden):
              ≥100 units → 20%  |  ≥50 → 10%  |  ≥20 → 5%  |  <20 → 0%
            Also checks whether requested quantity is in stock.
            """
            if quantity <= 0:
                return {"error": "Quantity must be a positive integer."}
            try:
                p = get_by_id(product_id)
                if p is None:
                    return {"error": f"Product not found: {product_id}"}
            except Exception as e:
                return {"error": f"Quote failed: {e}"}

            unit_price           = float(p.price)
            discount_rate, label = _resolve_discount(quantity)
            subtotal             = round(unit_price * quantity, 2)
            discount_amount      = round(subtotal * discount_rate, 2)
            total                = round(subtotal - discount_amount, 2)

            return {
                "product_id":      product_id,
                "product_name":    p.name,
                "quantity":        quantity,
                "unit_price":      round(unit_price, 2),
                "discount_pct":    int(discount_rate * 100),
                "discount_amount": discount_amount,
                "subtotal":        subtotal,
                "total":           total,
                "discount_rule":   label,
                "in_stock":        int(p.quantity) >= quantity,
                "stock_available": int(p.quantity),
            }

        @tool(args_schema=CompareProductsInput)
        def compare_products(product_ids: List[str]) -> list:
            """
            Fetch and compare multiple products side-by-side in one call.
            Pass a list of product IDs (get them via search_products first).
            Returns full details for each — useful for price or spec comparisons.
            """
            results = []
            for pid in product_ids[:10]:
                try:
                    p = get_by_id(pid)
                    if p is None:
                        results.append({"product_id": pid, "error": "Not found"})
                    else:
                        results.append({
                            "id":                 str(p.id),
                            "name":               p.name,
                            "brand":              p.brand,
                            "category":           p.category,
                            "unit_price":         float(p.price),
                            "quantity_available": int(p.quantity),
                            "description":        getattr(p, "description", ""),
                        })
                except Exception as e:
                    results.append({"product_id": pid, "error": str(e)})
            return results

        @tool(args_schema=MultiItemQuoteInput)
        def multi_item_quote(items: List[QuoteItem]) -> dict:
            """
            Calculate a quote for multiple products in one request.
            Each item must be: {"product_id": "...", "quantity": N}
            Returns per-item breakdown plus order_total and total_savings.
            Use this instead of calling calculate_quote repeatedly for basket orders.
            """
            line_items   = []
            order_total  = 0.0
            order_saving = 0.0
            errors       = []

            for item in items:
                pid = item.product_id
                qty = int(item.quantity)
                if qty <= 0:
                    errors.append({"product_id": pid, "error": "Quantity must be positive"})
                    continue
                try:
                    p = get_by_id(pid)
                    if p is None:
                        errors.append({"product_id": pid, "error": "Product not found"})
                        continue
                    unit_price           = float(p.price)
                    discount_rate, label = _resolve_discount(qty)
                    subtotal             = round(unit_price * qty, 2)
                    discount_amount      = round(subtotal * discount_rate, 2)
                    total                = round(subtotal - discount_amount, 2)
                    order_total         += total
                    order_saving        += discount_amount
                    line_items.append({
                        "product_id":      pid,
                        "product_name":    p.name,
                        "quantity":        qty,
                        "unit_price":      round(unit_price, 2),
                        "discount_pct":    int(discount_rate * 100),
                        "discount_amount": discount_amount,
                        "subtotal":        subtotal,
                        "total":           total,
                        "discount_rule":   label,
                    })
                except Exception as e:
                    errors.append({"product_id": pid, "error": str(e)})

            return {
                "line_items":    line_items,
                "errors":        errors,
                "order_total":   round(order_total, 2),
                "total_savings": round(order_saving, 2),
                "item_count":    len(line_items),
            }

        return [search_products, get_product_info, check_inventory, calculate_quote,
                compare_products, multi_item_quote]

    def _enrich(self, user_request: str, chat_history: Optional[List[Dict]] = None) -> str:
        if not RAG_AVAILABLE:
            history_lines = []
            for turn in (chat_history or [])[-5:]:
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                if role == "user":
                    history_lines.append(f"User: {content}")
                elif role == "assistant":
                    history_lines.append(f"Assistant: {content}")
            prefix = "\n".join(history_lines) + "\n\n" if history_lines else ""
            return f"{prefix}Current request: {user_request}"

        try:
            ctx = build_rag_context(user_request, chat_history or [])
            return (
                f"=== INVENTORY DATA ===\n{ctx['inventory_stats']}\n\n"
                f"=== PRODUCT CONTEXT ===\n{ctx['product_context']}\n\n"
                f"=== POLICY & DOCS ===\n{ctx['policy_context']}\n\n"
                f"=== CONVERSATION HISTORY ===\n{ctx['chat_history']}\n\n"
                f"Current request: {user_request}"
            )
        except Exception as exc:
            print(f"[agent] RAG enrichment failed: {exc}")
            return user_request

    def _build_result(self, agent_result: dict) -> dict:
        return {
            "response":   _extract_response_text(agent_result),
            "tool_calls": _extract_tool_calls(agent_result),
            "quote":      _extract_quote(agent_result),
            "trace_id":   str(uuid.uuid4()),
            "timestamp":  datetime.now().isoformat(),
        }

    @traceable(name="agent_chat", run_type="chain")
    def process_request(self, user_request: str, chat_history: Optional[List[Dict]] = None) -> dict:
        message = self._enrich(user_request, chat_history)
        result  = self.agent.invoke({"messages": [HumanMessage(content=message)]})
        return self._build_result(result)

    async def aprocess_request(
        self, user_request: str, chat_history: Optional[List[Dict]] = None
    ) -> AsyncIterator[dict]:
        yield {"type": "step", "step": "Retrieving context", "message": "Running RAG pipeline..."}

        # _enrich runs the full RAG pipeline in a thread so the event loop stays free.
        message = await asyncio.to_thread(self._enrich, user_request, chat_history)

        yield {"type": "step", "step": "Agent reasoning", "message": "Running ReAct agent..."}

        try:
            result = await asyncio.to_thread(
                self.agent.invoke,
                {"messages": [HumanMessage(content=message)]}
            )
            payload = self._build_result(result)
            # Emit tool call steps for the UI
            for tc in payload["tool_calls"]:
                yield {"type": "step", "step": f"Tool: {tc['tool']}", "message": str(tc.get("args", {}))}

            yield {"type": "result", "data": payload}

        except Exception as e:
            yield {"type": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    def generate_quote_invoice(self, quote_data: dict | list) -> dict:
        """Accept either a single quote dict or a list of line items."""
        items = quote_data if isinstance(quote_data, list) else [quote_data]
        total_amount   = round(sum(i.get("total", 0) for i in items), 2)
        total_discount = round(sum(i.get("discount_amount", 0) for i in items), 2)
        return {
            "invoice_id":     f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp":      datetime.now().isoformat(),
            "items":          items,
            "item_count":     len(items),
            "total_amount":   total_amount,
            "total_discount": total_discount,
            "net_payable":    total_amount,
        }

    def rag_chat_only(self, message: str, chat_history: Optional[List[Dict]] = None) -> dict:
        if not RAG_AVAILABLE:
            return {"response": "RAG not available.", "trace_id": str(uuid.uuid4()), "success": False}
        try:
            from django_app.domain.rag_service import rag_chat_with_tracing
            return rag_chat_with_tracing(message, chat_history or [])
        except Exception as e:
            return {"response": f"Error: {e}", "trace_id": str(uuid.uuid4()), "success": False}