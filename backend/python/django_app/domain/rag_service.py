from __future__ import annotations

import asyncio
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

from django_app.domain.rag_retriever import RetrievalResult, retrieve

try:
    from django_app.domain import stock_event_service
    STOCK_EVENTS_AVAILABLE = True
except ImportError:
    STOCK_EVENTS_AVAILABLE = False

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY", ""),
    temperature=0.3,
    timeout=30,
)

_expansion_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY", ""),
    temperature=0.0,   # expansion is deterministic
    timeout=15,
    max_output_tokens=256,
)

_PROMPT_TEMPLATE = """You are an intelligent inventory management assistant.

You have access to three sources of information — use the most relevant one(s) to answer:

1. INVENTORY DATA — complete live snapshot: totals, rankings by price and stock, low-stock alerts, all categories and brands. Use this for any question involving numbers, rankings, comparisons, or overviews.
2. SEMANTIC PRODUCT CHUNKS — specific product details retrieved for this query. Use for targeted product questions.
3. POLICY & DOCS — warranties, return windows, refund rules, FAQs. Use for policy questions.

Rules:
- Be concise and factual.
- Format prices as ₹X,XX,XXX.
- If the answer is not in the data below, say so clearly.

=== INVENTORY DATA ===
{inventory_stats}

=== SEMANTIC PRODUCT CHUNKS ===
{product_context}

=== POLICY & DOCS ===
{policy_context}

=== CONVERSATION HISTORY ===
{chat_history}

User Question: {question}

Answer:"""


def _format_chat_history(chat_history: List[Dict]) -> str:
    lines = []
    for msg in chat_history[-5:]:
        prefix = "User" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{prefix}: {msg.get('content', '')}")
    return "\n".join(lines) or "No previous conversation."


_EXPANSION_PROMPT = """You are an expert search query expander for an inventory management system.
 
The system contains:
- PRODUCTS: physical items with names, brands, categories, prices, stock quantities, and descriptions
- POLICIES: return windows, refund rules, exchange conditions, damage claims
- WARRANTIES: warranty periods, coverage details, claim procedures
- FAQs: vendor questions, general usage, shipping, support
 
Your job is to decompose the user's message into 3-6 search queries that together retrieve everything needed for a complete answer. Each query targets a distinct angle — never repeat the same concept twice.
 
Queries are used for semantic vector search, so longer and more descriptive queries work better than short keyword queries. Pack each query with relevant context, intent, and descriptive terms so the embedding captures the full meaning.
 
Think about:
- What specific products or product categories are relevant, including synonyms and related names?
- Are there alternative or complementary products the user might not have mentioned but would need?
- Are there policies, warranties, or FAQs that apply to this situation?
- Are there use-case, compatibility, or application-specific angles?
- Are there price, stock, brand, or availability angles worth covering?
- If the user describes a goal or project, what are all the individual items or information pieces needed?
 
Output Rules:
- One query per line
- No numbering, bullets, labels, or explanation — raw queries only
- Queries must be distinct — do not paraphrase the same idea
- Make queries descriptive and context-rich — longer is better for semantic search
- Include relevant synonyms, use-cases, and technical terms in each query
 
Examples:
User: can I return a damaged product and get a refund
Output:
return policy for damaged defective or broken products
refund eligibility conditions and process for damaged items
warranty coverage and claim procedure for defective goods
exchange or replacement policy for items damaged on arrival
how to initiate a return or refund request for damaged product
 
User: what is the most affordable wireless audio option
Output:
budget friendly wireless bluetooth earphones and headphones low price
affordable in-ear wireless earbuds with good sound quality
cheapest bluetooth headphones with mic available in stock
entry level wireless audio options price comparison

User: what is your return policy for electronics
Output:
return policy terms and conditions for electronic products
how many days do I have to return electronics after purchase
refund process and timeline for returned electronic items
conditions under which electronics can be exchanged or replaced
what happens if electronics stop working shortly after purchase
 
User: show me all cameras and accessories
Output:
digital cameras DSLR mirrorless point and shoot available in stock
camera lenses wide angle telephoto zoom accessories
memory cards SD cards high speed storage for cameras
camera tripods stands stabilizers and mounts
camera bags cases and protective covers
lens filters UV polarizer neutral density accessories
 
User message: {message}
Output:"""
 

def _expand_queries(message: str) -> List[str]:
    try:
        response = _expansion_llm.invoke(_EXPANSION_PROMPT.format(message=message))
        lines = [l.strip() for l in response.content.strip().splitlines() if l.strip()]
        queries = list(dict.fromkeys([message] + lines))
        return queries[:6]
    except Exception as exc:
        print(f"[rag_chat] query expansion failed, using original: {exc}")
        return [message]


def _enrich_query_from_history(message: str, chat_history: List[Dict]) -> str:
    if not chat_history:
        return message

    reference_signals = ["their", "its", "it", "these", "those", "them", "the product",
                         "same", "what about", "how about", "and the", "also"]
    if not any(s in message.lower() for s in reference_signals):
        return message

    last_assistant = next(
        (m.get("content", "") for m in reversed(chat_history) if m.get("role") == "assistant"),
        ""
    )
    if not last_assistant:
        return message

    words = last_assistant.split()
    proper_chunks = []
    current = []

    for word in words:
        cleaned = word.strip(".,;:()'\"" )
        if cleaned and (cleaned[0].isupper() or any(c.isdigit() for c in cleaned)):
            current.append(cleaned)
        else:
            if len(current) >= 2:
                proper_chunks.append(" ".join(current))
            current = []
    if len(current) >= 2:
        proper_chunks.append(" ".join(current))

    seen = set()
    product_names = []
    for chunk in proper_chunks:
        key = chunk.lower()
        if key not in seen and len(chunk.split()) <= 5:
            seen.add(key)
            product_names.append(chunk)

    if not product_names:
        return message

    injected = ", ".join(product_names[:4])
    return f"{message} [{injected}]"


@traceable(name="rag_chat", run_type="chain")
def rag_chat(message: str, chat_history: Optional[List[Dict]] = None) -> str:
    if chat_history is None:
        chat_history = []

    try:
        base_query = _enrich_query_from_history(message, chat_history)
        queries    = _expand_queries(base_query)
        result: RetrievalResult = retrieve(queries)

        prompt_kwargs = {
            "inventory_stats": result.inventory_stats or "Unavailable.",
            "product_context": result.product_context,
            "policy_context":  result.policy_context,
            "chat_history":    _format_chat_history(chat_history),
            "question":        message,
        }

        chain = PromptTemplate(
            template=_PROMPT_TEMPLATE,
            input_variables=list(prompt_kwargs.keys()),
        ) | llm

        try:
            response = chain.invoke(prompt_kwargs)
        except Exception as exc:
            err = str(exc)
            if "missing" in err and "variables" in err:
                for var in re.findall(r"'([^']+)'", err):
                    prompt_kwargs.setdefault(var, "")
                response = chain.invoke(prompt_kwargs)
            else:
                raise

        return response.content

    except Exception as exc:
        return f"I encountered an error: {exc}. Please try again."

def get_stock_events_ctx(): 
    stock_events_ctx = ""
    if STOCK_EVENTS_AVAILABLE:
        try:
            summary = stock_event_service.get_event_summary()
            upcoming = stock_event_service.get_upcoming_events(14)  # Next 2 weeks
            stock_events_ctx = f"""STOCK EVENTS SUMMARY:
- Total events: {summary['total']} (Pending: {summary['pending']}, Completed: {summary['completed']})
- Upcoming (7 days): {summary['upcoming_7_days']} events
- Upcoming (30 days): {summary['upcoming_30_days']} events
- By Priority: Critical: {summary['by_priority']['Critical']}, High: {summary['by_priority']['High']}, Medium: {summary['by_priority']['Medium']}, Low: {summary['by_priority']['Low']}

NEXT 14 DAYS UPCOMING EVENTS:
"""
            for e in upcoming[:10]:
                products_summary = ""
                if e.products:
                    product_details = []
                    for p in e.products[:3]:
                        pname = p.get("product_name", "Unknown")
                        qty = p.get("quantity_change", 0)
                        product_details.append(f"{pname} ({qty:+d})")
                    products_summary = ", ".join(product_details)
                    if len(e.products) > 3:
                        products_summary += f" +{len(e.products) - 3} more"
                stock_events_ctx += f"- [{e.priority}] {e.event_type}: {products_summary or 'No products'} on {e.expected_date}\n"
        except Exception as exc:
            stock_events_ctx = f"Stock events unavailable: {exc}"
    return stock_events_ctx

def build_rag_context(message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
    if chat_history is None:
        chat_history = []
    try:
        base_query = _enrich_query_from_history(message, chat_history)

        # Run query expansion and vector store warm-up concurrently.
        # get_vector_store() is cheap when the store is already cached; calling it
        # here in parallel with the LLM expansion call hides any remaining cache
        # check latency behind the expansion network round-trip.
        with ThreadPoolExecutor(max_workers=2) as ex:
            future_queries = ex.submit(_expand_queries, base_query)
            future_store   = ex.submit(_ensure_store_ready)
            queries = future_queries.result()
            future_store.result()  # ensure store is warm before retrieve()

        result: RetrievalResult = retrieve(queries)
        return {
            "inventory_stats": result.inventory_stats or "Unavailable.",
            "stock_events" : get_stock_events_ctx(),
            "product_context": result.product_context,
            "policy_context":  result.policy_context,
            "chat_history":    _format_chat_history(chat_history),
        }
    except Exception as exc:
        print(f"[rag] build_rag_context failed: {exc}")
        return {
            "inventory_stats": "Unavailable.",
            "stock_events" : "Unavailable.",
            "product_context": "Unavailable.",
            "policy_context":  "Unavailable.",
            "chat_history":    _format_chat_history(chat_history),
        }


def _ensure_store_ready() -> None:
    try:
        from django_app.domain.rag_retriever import get_vector_store
        get_vector_store()
    except Exception as exc:
        print(f"[rag] store warm-up failed: {exc}")


def rag_chat_with_tracing(message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
    if chat_history is None:
        chat_history = []

    trace_id = str(uuid.uuid4())
    try:
        response = rag_chat(message, chat_history)
        return {"response": response, "trace_id": trace_id, "success": True}
    except Exception as exc:
        return {
            "response": f"I encountered an error: {exc}. Please try again.",
            "trace_id": trace_id,
            "success": False,
            "error": str(exc),
        }


@traceable(name="generate_chat_title", run_type="llm")
def generate_chat_title(first_message: str) -> str:
    try:
        title = llm.invoke(
            f'Generate a concise 3-5 word title for a conversation starting with:\n"{first_message}"\nOutput ONLY the title.'
        ).content.strip().strip("\"'")
        words = title.split()
        return (" ".join(words[:5]) + ("..." if len(words) > 5 else "")) or "New Chat"
    except Exception:
        words = first_message.split()[:5]
        return " ".join(words) + ("..." if len(first_message.split()) > 5 else "") or "New Chat"