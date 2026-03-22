from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

SENTENCE_WINDOW = 2
RETRIEVE_K      = 6
FETCH_K         = 30
MMR_LAMBDA      = 0.55
PRODUCT_TTL     = 300
PERSIST_DIR     = "./chroma_db"

_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

_semantic_splitter = SemanticChunker(
    embeddings=_embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=85,
)

_para_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
)

_store: Optional[Chroma] = None
_product_built_at: float  = 0.0
_product_hash: str        = ""
_cached_products: list    = []      # shared across retrieve() and get_vector_store()


def _fingerprint(docs: List[Document]) -> str:
    return hashlib.md5("".join(d.page_content for d in docs).encode()).hexdigest()


def _cheap_product_fingerprint() -> str:
    try:
        from django_app.domain.product_service import list_products
        products, _ = list_products(page=1, page_size=1000)
        key = "|".join(
            f"{p.id}:{p.name}:{p.price}:{p.quantity}"
            for p in sorted(products, key=lambda p: str(p.id))
        )
        return hashlib.md5(key.encode()).hexdigest()
    except Exception as exc:
        print(f"[retriever] cheap fingerprint failed: {exc}")
        return str(time.time())


def _prepend_header(text: str, header: str) -> str:
    return f"[{header}] {text}"


def _build_sentence_window_docs(sentences: List[str], base_metadata: dict) -> List[Document]:
    import json
    docs = []
    header = base_metadata.get("type", "Document")
    serialized = json.dumps(sentences)
    for i, sentence in enumerate(sentences):
        docs.append(Document(
            page_content=_prepend_header(sentence.strip(), header),
            metadata={**base_metadata, "sentence_index": i, "all_sentences": serialized},
        ))
    return docs


def _expand_window(doc: Document) -> Document:
    import json
    raw = doc.metadata.get("all_sentences")
    if not raw:
        return doc
    try:
        sentences = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return doc
    idx   = doc.metadata.get("sentence_index", 0)
    start = max(0, idx - SENTENCE_WINDOW)
    end   = min(len(sentences), idx + SENTENCE_WINDOW + 1)
    return Document(
        page_content=" ".join(sentences[start:end]),
        metadata={k: v for k, v in doc.metadata.items() if k not in ("all_sentences", "sentence_index")},
    )


def _load_text_docs() -> List[Document]:
    from django.conf import settings
    docs_dir = os.path.join(settings.BASE_DIR, "django_app", "static", "docs")
    docs = []
    for filename, doc_type in [
        ("product_manual.txt", "Product Manual"),
        ("return_policy.txt",  "Return Policy"),
        ("vendor_faqs.txt",    "Vendor FAQs"),
    ]:
        path = os.path.join(docs_dir, filename)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        base_meta = {"source": filename, "type": doc_type}
        semantic_chunks = _semantic_splitter.split_text(content)
        docs.extend(_build_sentence_window_docs(semantic_chunks, base_meta))
    return docs


def _load_product_docs() -> List[Document]:
    try:
        from django_app.domain.product_service import list_products
        products, _ = list_products(page=1, page_size=1000)
        docs = []
        for p in products:
            policy  = p.policy or {}
            content = _prepend_header(
                f"Product: {p.name}\nBrand: {p.brand}\nCategory: {p.category}\n"
                f"Price: ₹{p.price}\nQuantity in stock: {p.quantity}\n"
                f"Description: {p.description or 'N/A'}\n"
                f"Warranty: {policy.get('warranty_period', 'N/A')}\n"
                f"Return Window: {policy.get('return_window', 'N/A')}\n"
                f"Refund Policy: {policy.get('refund_policy', 'N/A')}",
                f"Product | {p.category}",
            )
            meta = {
                "source": "product_db", "type": "product",
                "product_id": str(p.id), "product_name": p.name,
                "category": p.category, "price": float(p.price), "quantity": int(p.quantity),
            }
            semantic_chunks = _semantic_splitter.split_text(content)
            chunks = semantic_chunks if len(semantic_chunks) > 1 else _para_splitter.split_text(content)
            for chunk in chunks:
                docs.append(Document(page_content=chunk, metadata=meta))
        return docs
    except Exception as exc:
        print(f"[retriever] product load failed: {exc}")
        return []


def _refresh_product_cache() -> None:
    global _cached_products
    try:
        from django_app.domain.product_service import list_products
        products, _ = list_products(page=1, page_size=1000)
        _cached_products = products
    except Exception as exc:
        print(f"[retriever] product cache refresh failed: {exc}")


def get_vector_store(force_rebuild: bool = False) -> Optional[Chroma]:
    global _store, _product_built_at, _product_hash

    if _store is None or force_rebuild:
        product_docs      = _load_product_docs()
        all_docs          = _load_text_docs() + product_docs
        _store            = Chroma.from_documents(all_docs, _embeddings, persist_directory=PERSIST_DIR)
        _product_built_at = time.time()
        _product_hash     = _cheap_product_fingerprint()
        _refresh_product_cache()
        return _store

    if time.time() - _product_built_at <= PRODUCT_TTL:
        return _store

    current_hash = _cheap_product_fingerprint()
    if current_hash == _product_hash:
        _product_built_at = time.time()
        return _store  # products unchanged; cache still valid

    try:
        product_docs = _load_product_docs()
        existing     = _store.get(where={"source": "product_db"})
        if existing.get("ids"):
            _store.delete(ids=existing["ids"])
        if product_docs:
            _store.add_documents(product_docs)
        _product_built_at = time.time()
        _product_hash     = current_hash
        _refresh_product_cache()
    except Exception as exc:
        print(f"[retriever] product refresh failed: {exc}")

    return _store


def _dedup(docs: List[Document]) -> List[Document]:
    seen, result = set(), []
    for doc in docs:
        key = hashlib.md5(doc.page_content.strip().encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            result.append(doc)
    return result


def _get_inventory_products() -> list:
    return _cached_products


def _build_inventory_context(products: list) -> str:
    if not products:
        return ""

    total_value   = sum(p.price * p.quantity for p in products)
    avg_price     = sum(p.price for p in products) / len(products)
    low_stock     = [p for p in products if p.quantity <= 5]
    categories    = list({p.category for p in products})
    brands        = list({p.brand for p in products})
    by_price_desc = sorted(products, key=lambda p: p.price, reverse=True)
    by_price_asc  = sorted(products, key=lambda p: p.price)
    by_qty_asc    = sorted(products, key=lambda p: p.quantity)
    by_qty_desc   = sorted(products, key=lambda p: p.quantity, reverse=True)

    def fmt(p):
        return f"{p.name} ({p.brand}) | ₹{p.price} | {p.quantity} units | {p.category}"

    lines = [
        f"Total products: {len(products)} | Inventory value: ₹{total_value:,.2f} | Avg price: ₹{avg_price:.2f}",
        f"Categories: {', '.join(categories)}",
        f"Brands: {', '.join(brands)}",
        "",
        "Most expensive:", *[f"  {i+1}. {fmt(p)}" for i, p in enumerate(by_price_desc[:5])],
        "",
        "Cheapest:",       *[f"  {i+1}. {fmt(p)}" for i, p in enumerate(by_price_asc[:5])],
        "",
        "Highest stock:",  *[f"  {i+1}. {fmt(p)}" for i, p in enumerate(by_qty_desc[:5])],
        "",
        "Lowest stock:",   *[f"  {i+1}. {fmt(p)}" for i, p in enumerate(by_qty_asc[:5])],
    ]

    if low_stock:
        lines += ["", f"Low stock alert (≤5 units) — {len(low_stock)} product(s):"]
        lines += [f"  • {p.name} ({p.brand}): {p.quantity} units" for p in low_stock[:10]]

    return "\n".join(lines)


@dataclass
class RetrievalResult:
    product_docs:    List[Document]
    policy_docs:     List[Document]
    inventory_stats: str

    @property
    def policy_context(self) -> str:
        return "\n\n".join(d.page_content for d in self.policy_docs) or "No documentation retrieved."

    @property
    def product_context(self) -> str:
        return "\n\n".join(d.page_content for d in self.product_docs) or "No product information retrieved."


@traceable(name="retrieve", run_type="retriever")
def retrieve(queries) -> RetrievalResult:
    products  = _get_inventory_products()
    inv_stats = _build_inventory_context(products)

    if isinstance(queries, str):
        queries = [queries]

    store = get_vector_store()
    docs: List[Document] = []

    if store:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _search(q: str) -> List[Document]:
            try:
                return store.max_marginal_relevance_search(
                    q, k=RETRIEVE_K, fetch_k=FETCH_K, lambda_mult=MMR_LAMBDA
                )
            except Exception as exc:
                print(f"[retriever] query failed '{q}': {exc}")
                return []

        raw: List[Document] = []
        with ThreadPoolExecutor(max_workers=min(len(queries), 4)) as ex:
            futures = {ex.submit(_search, q): q for q in queries}
            for fut in as_completed(futures):
                raw.extend(fut.result())

        expanded = [_expand_window(d) if d.metadata.get("all_sentences") else d for d in raw]
        docs     = _dedup(expanded)

    return RetrievalResult(
        product_docs=[d for d in docs if d.metadata.get("type") == "product"],
        policy_docs=[d for d in docs if d.metadata.get("type") != "product"],
        inventory_stats=inv_stats,
    )


def get_inventory_stats() -> Dict:
    try:
        from django_app.domain.product_service import list_products
        products, total_count = list_products(page=1, page_size=1000)
        if not products:
            return {}

        categories = list({p.category for p in products})
        return {
            "total_products":  total_count,
            "total_quantity":  sum(p.quantity for p in products),
            "inventory_value": sum(p.price * p.quantity for p in products),
            "avg_price":       sum(p.price for p in products) / len(products),
            "categories":      categories,
            "brands":          list({p.brand for p in products}),
            "category_stats": {
                cat: {
                    "count":          len(cp := [p for p in products if p.category == cat]),
                    "total_quantity": sum(p.quantity for p in cp),
                    "total_value":    sum(p.price * p.quantity for p in cp),
                }
                for cat in categories
            },
            "low_stock_products": [
                {"name": p.name, "quantity": p.quantity, "brand": p.brand, "category": p.category}
                for p in products if p.quantity <= 5
            ],
        }
    except Exception as exc:
        print(f"[retriever] stats error: {exc}")
        return {}