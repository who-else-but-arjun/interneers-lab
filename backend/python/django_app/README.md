# Inventory RAG Agent

A Django-based AI backend combining a full RAG pipeline with a LangGraph ReAct agent. Every request runs retrieval first — the agent receives pre-fetched inventory data, product chunks, and policy docs before it starts reasoning, and only calls tools when the context is insufficient.

---

## Architecture Overview

```
Client
  │
  ├── /rag/chat/       →  Pure RAG Q&A
  │                         └── Query Expansion → Retriever → Gemini LLM
  │
  └── /agent/chat/    →  RAG-ReAct Agent
                            └── build_rag_context() → Agent Loop → Tools → Gemini LLM
```

Both modes share the same retrieval layer. The agent runs the full RAG pipeline as a pre-step before the ReAct loop begins, so it can answer many questions directly from context without making any tool calls.

---

## RAG Pipeline

Defined in `rag_service.py` and `rag_retriever.py`. Used directly by `/rag/chat/` and as the enrichment step for the agent.

### 1. Query Enrichment

If the user's message contains reference words (`it`, `their`, `same`, `what about`, etc.), the last assistant turn is scanned for product names and they are injected into the query before retrieval. This resolves coreferences so follow-up questions like "how much does it cost?" retrieve the right product.

### 2. Query Expansion

The enriched query is sent to the LLM, which expands it into 3–6 semantically distinct sub-queries covering different angles — synonyms, related categories, policy angles, price/stock angles, use-case variations. All sub-queries run against the vector store, maximising recall.

### 3. Retrieval

The retriever maintains a Chroma vector store built from two sources:

**Static docs** — `product_manual.txt`, `return_policy.txt`, `vendor_faqs.txt`. Each file is split with a semantic chunker (percentile-based breakpoints) and stored with sentence-window metadata. At query time, each retrieved chunk is expanded by merging its neighbouring sentences, giving the LLM wider context without bloating the index.

**Live product DB** — all products fetched from Django ORM, serialised with name, brand, category, price, stock, warranty, and return policy, then semantically chunked and embedded.

Each sub-query runs MMR (Maximal Marginal Relevance) search. Results are deduplicated across queries before being split into `product_docs` and `policy_docs`.

### 4. Vector Store Cache

A two-tier cache avoids unnecessary reloads on every request:

- Within the TTL window (default 5 min) — store returned immediately, zero DB calls.
- After TTL expiry — a cheap fingerprint query fetches only `id`, `name`, `price`, `quantity` per product and hashes them. If unchanged, TTL clock resets and store is returned.
- Only if the fingerprint differs does the full product reload and re-indexing run.

### 5. `build_rag_context()`

A shared function that packages the entire pipeline into a structured dict:

```python
{
    "inventory_stats": "...",   # live snapshot: totals, rankings, low-stock alerts
    "product_context": "...",   # semantic product chunks for this query
    "policy_context":  "...",   # policy/warranty/FAQ chunks
    "chat_history":    "...",   # last 5 turns formatted
}
```

This is the single entry point used by both the RAG chat and the agent.

---

**Chunking Strategies**

Two strategies are applied depending on document type.

**Semantic Chunking** (`SemanticChunker`, primary) embeds every sentence and places chunk boundaries where cosine similarity between adjacent sentences drops below the 85th percentile threshold. Breaks only happen when the topic genuinely shifts — related sentences stay together. Applied to both static docs and products. For products, if the entire content stays as one semantic unit, the recursive splitter is used as a size-ceiling fallback.

**Recursive Character Splitting** (fallback) splits at paragraph → line → sentence → space boundaries, producing chunks of max 500 characters with 50-character overlap. Used only when semantic chunking doesn't split a product entry.

**Sentence-Window Storage** (static docs only) stores each semantic chunk individually with `sentence_index` and `all_sentences` metadata. At retrieval time `_expand_window()` merges ±2 neighbouring chunks before passing the result to the LLM. The index stores small atomic units for precise retrieval; the LLM receives the surrounding context for comprehension.

**Context Header Prepending** — every chunk is stored with a domain header (`[Product | Electronics]`, `[Return Policy]`, etc.) so product and policy embeddings occupy distinct regions of the vector space, reducing cross-type false positives.

---

**Retrieval Strategies**

**MMR (Maximal Marginal Relevance)** selects chunks that are relevant to the query but dissimilar from each other, avoiding near-duplicate results. `lambda_mult = 0.55` leans slightly toward relevance over diversity. `FETCH_K = 30` candidates are fetched and MMR selects the best `RETRIEVE_K = 6`.

**Multi-Query Retrieval** — each message is expanded into 3–6 sub-queries and MMR runs independently for each, producing up to 36 raw candidates before deduplication. This maximises recall regardless of how the user phrased the question.

**Deduplication** — results are pooled across all sub-queries and deduplicated by MD5 content hash, preventing the same chunk from appearing multiple times in the context window.

**Result Separation** — deduplicated chunks are split into `product_docs` and `policy_docs` by their `type` metadata and injected into distinct labelled prompt sections, preventing the LLM from conflating the two.

**Live Inventory Stats** — alongside vector retrieval, `_build_inventory_context()` runs a direct DB query and builds a structured snapshot (totals, top-5 rankings, low-stock alerts). This answers aggregate questions like "what are our top 5 most expensive products?" with certainty — vector search handles these poorly because an aggregate query doesn't strongly match any individual product chunk.
## ReAct Agent

Defined in `quote_agent_service.py`. Uses LangGraph's `create_react_agent` with Gemini 2.5 Flash.

### Enrichment Before Reasoning

Before the ReAct loop starts, `_enrich()` calls `build_rag_context()` and formats the result into labelled sections prepended to the user message:

```
=== INVENTORY DATA ===
...live snapshot...

=== PRODUCT CONTEXT ===
...semantic product chunks...

=== POLICY & DOCS ===
...policy documentation...

=== CONVERSATION HISTORY ===
...last 5 turns...

Current request: <user message>
```

The agent's system prompt instructs it to answer directly from these sections when possible, and only reach for tools when the context is insufficient.

### When the Agent Answers Without Tools

- Inventory overviews, rankings, totals → **INVENTORY DATA**
- Policy, warranty, return questions → **POLICY & DOCS**
- Product descriptions already retrieved → **PRODUCT CONTEXT**

### When the Agent Uses Tools

| Tool | Trigger |
|---|---|
| `search_products` | Product mentioned by name, not found in PRODUCT CONTEXT |
| `get_product_info` | Full details needed and ID already known |
| `check_inventory` | User explicitly asks about current stock level |
| `calculate_quote` | Quantity + price calculation for a single product |
| `compare_products` | Side-by-side comparison for multiple products |
| `multi_item_quote` | Basket order — multiple products + quantities in one call |

### Discount Tiers

Enforced in `_resolve_discount()`, cannot be overridden by the LLM:

| Quantity | Discount |
|---|---|
| < 20 units | 0% |
| ≥ 20 units | 5% |
| ≥ 50 units | 10% |
| ≥ 100 units | 20% (max) |

### Fuzzy Product Search

`search_products` matches via three strategies in order: substring match, all-words match, trigram similarity (≥ 30% overlap). Handles partial names, misspellings, and multi-word queries.

### Streaming

`agent_chat_stream` runs the async generator in a background thread and pushes events into a `queue.Queue`. The Django `StreamingHttpResponse` iterator drains the queue as events arrive, giving true progressive SSE output. Events:

```
{"type": "step",   "step": "Retrieving context", "message": "Running RAG pipeline..."}
{"type": "step",   "step": "Agent reasoning",    "message": "Running ReAct agent..."}
{"type": "step",   "step": "Tool: search_products", "message": "{...args...}"}
{"type": "result", "data": { ...full result... }}
{"type": "error",  "error": "..."}
```

---

## Data Flow

### RAG chat request

```
POST /rag/chat/
  │
  ├─ _enrich_query_from_history()    coreference resolution
  ├─ _expand_queries()               3–6 sub-queries via LLM
  ├─ retrieve()
  │    ├─ get_vector_store()         two-tier cache check
  │    ├─ MMR search per sub-query
  │    ├─ sentence-window expansion
  │    └─ dedup → product_docs + policy_docs
  ├─ _build_inventory_context()      live DB stats snapshot
  ├─ fill prompt template
  └─ Gemini LLM → response
```

### Agent chat request

```
POST /agent/chat/
  │
  ├─ build_rag_context()             full RAG pipeline (same as above)
  │    └─ returns inventory_stats, product_context, policy_context, chat_history
  ├─ _enrich()                       format into labelled sections
  ├─ LangGraph ReAct loop
  │    ├─ LLM reads context, reasons
  │    ├─ if context sufficient → final answer (no tool call)
  │    ├─ else → emit tool call → execute → result back to LLM
  │    └─ repeat until final answer
  └─ extract response, tool_calls, quote → JsonResponse
```

---

## API Endpoints

### RAG

| Method | Path | Description |
|---|---|---|
| POST | `/rag/chat/` | RAG Q&A with chat history |
| POST | `/rag/generate-title/` | Generate short title for a conversation |
| GET | `/rag/chats/` | List saved chat sessions |
| POST | `/rag/chats/` | Create a new chat session |
| GET | `/rag/chats/<id>/` | Get a chat session |
| PUT | `/rag/chats/<id>/` | Update messages/title |
| DELETE | `/rag/chats/<id>/` | Delete a chat session |
| POST | `/rag/chats/sync/` | Bulk sync local chats to server |

### Agent

| Method | Path | Description |
|---|---|---|
| POST | `/agent/chat/` | Synchronous agent response |
| POST | `/agent/chat/stream/` | Streaming SSE agent response |
| POST | `/agent/search/` | Direct product search (no LLM) |
| GET | `/agent/status/` | Agent health, available tools, config |
| GET | `/agent/chats/` | List saved chat sessions |
| POST | `/agent/chats/` | Create a new chat session |
| GET | `/agent/chats/<id>/` | Get a chat session |
| PUT | `/agent/chats/<id>/` | Update messages/title |
| DELETE | `/agent/chats/<id>/` | Delete a chat session |
| POST | `/agent/chats/sync/` | Bulk sync local chats to server |

### Payloads

**RAG chat**
```json
// Request
{ "message": "What is the return policy for electronics?", "chat_history": [] }

// Response
{ "success": true, "response": "...", "trace_id": "uuid", "trace_url": "..." }
```

**Agent chat**
```json
// Request
{ "message": "I need 60 NodeMCU boards, what's the total?", "chat_history": [] }

// Response
{
  "status": "success",
  "response": "For 60 NodeMCU boards at ₹450 each...",
  "tool_calls": [{ "tool": "search_products", "args": { "query": "NodeMCU" } }],
  "quote": { "product_name": "NodeMCU", "quantity": 60, "total": 24300.0, "discount_pct": 10 },
  "trace_id": "uuid"
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Django |
| LLM | Gemini 2.5 Flash (`langchain-google-genai`) |
| Agent framework | LangGraph (`create_react_agent`) |
| Vector store | Chroma (persisted to `./chroma_db`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Text splitting | LangChain `SemanticChunker` + `RecursiveCharacterTextSplitter` |
| Chat persistence | MongoDB |
| Tracing | LangSmith |

---