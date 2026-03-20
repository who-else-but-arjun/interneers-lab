import hashlib
import json
import time

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from django_app.domain import product_service
from django_app.domain.semantic_search import semantic_search
from django_app.adapters.product_views import _product_to_dict

_PRODUCT_CACHE_TTL = 60

_cached_product_dicts = []
_cached_at = 0.0


def _get_product_dicts() -> list:
    global _cached_product_dicts, _cached_at
    if time.time() - _cached_at < _PRODUCT_CACHE_TTL and _cached_product_dicts:
        return _cached_product_dicts
    products, _ = product_service.list_products(page=1, page_size=1000, category_ids=None)
    _cached_product_dicts = [_product_to_dict(p) for p in products]
    _cached_at = time.time()
    semantic_search.index_products(_cached_product_dicts)
    return _cached_product_dicts


@csrf_protect
@require_http_methods(["POST"])
def semantic_search_products(request):
    try:
        data            = json.loads(request.body)
        query           = data.get("query", "").strip()
        top_k           = min(int(data.get("top_k", 10)), 50)
        category_filter = data.get("category_filter", None)

        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)

        product_dicts = _get_product_dicts()

        if category_filter:
            filtered = [p for p in product_dicts if p.get("category") == category_filter]
            semantic_search.index_products(filtered)
            results = semantic_search.search(query, top_k=top_k)
            semantic_search.index_products(product_dicts)
        else:
            results = semantic_search.search(query, top_k=top_k)

        return JsonResponse({
            "query":         query,
            "results":       [
                {"product": product, "similarity_score": round(float(score), 4)}
                for product, score in results
            ],
            "total_results": len(results),
        })

    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def find_similar_products(request):
    try:
        data       = json.loads(request.body)
        product_id = data.get("product_id", "").strip()
        top_k      = min(int(data.get("top_k", 5)), 20)

        if not product_id:
            return JsonResponse({"error": "Product ID is required"}, status=400)

        _get_product_dicts()
        results = semantic_search.find_similar_products(product_id, top_k=top_k)

        return JsonResponse({
            "product_id":      product_id,
            "similar_products": [
                {"product": product, "similarity_score": round(float(score), 4)}
                for product, score in results
            ],
            "total_results": len(results),
        })

    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def hybrid_search(request):
    try:
        data            = json.loads(request.body)
        query           = data.get("query", "").strip()
        semantic_weight = float(data.get("semantic_weight", 0.7))
        keyword_weight  = float(data.get("keyword_weight", 0.3))
        top_k           = min(int(data.get("top_k", 10)), 50)

        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)

        product_dicts = _get_product_dicts()
        query_lower   = query.lower()

        keyword_scores = {}
        for p in product_dicts:
            text  = f"{p.get('name', '')} {p.get('description', '')} {p.get('category', '')}".lower()
            score = 0.0
            if query_lower in text:
                score = 1.5 if query_lower in p.get("name", "").lower() else 1.0
            keyword_scores[p.get("id")] = score

        max_kw = max(keyword_scores.values(), default=1) or 1
        keyword_scores = {pid: s / max_kw for pid, s in keyword_scores.items()}

        semantic_results = semantic_search.search(query, top_k=len(product_dicts))

        combined = {}
        for product, sem_score in semantic_results:
            pid = product.get("id")
            kw  = keyword_scores.get(pid, 0.0)
            combined[pid] = {
                "product":        product,
                "semantic_score": sem_score,
                "keyword_score":  kw,
                "combined_score": semantic_weight * sem_score + keyword_weight * kw,
            }

        for pid, kw in keyword_scores.items():
            if pid not in combined and kw > 0:
                for p in product_dicts:
                    if p.get("id") == pid:
                        combined[pid] = {
                            "product":        p,
                            "semantic_score": 0.0,
                            "keyword_score":  kw,
                            "combined_score": keyword_weight * kw,
                        }
                        break

        sorted_results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)

        return JsonResponse({
            "query":           query,
            "semantic_weight": semantic_weight,
            "keyword_weight":  keyword_weight,
            "results": [
                {
                    "product":        r["product"],
                    "semantic_score": round(float(r["semantic_score"]), 4),
                    "keyword_score":  round(float(r["keyword_score"]),  4),
                    "combined_score": round(float(r["combined_score"]), 4),
                }
                for r in sorted_results[:top_k]
            ],
            "total_results": len(sorted_results),
        })

    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)