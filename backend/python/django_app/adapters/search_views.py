import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django_app.domain import product_service
from django_app.domain.semantic_search import semantic_search
from django_app.adapters.product_views import _product_to_dict

@csrf_protect
@require_http_methods(["POST"])
def semantic_search_products(request):
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        top_k = min(int(data.get("top_k", 10)), 50)
        category_filter = data.get("category_filter", None)
        
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)
        
        products, _ = product_service.list_products(page=1, page_size=1000, category_ids=None)
        product_dicts = [_product_to_dict(p) for p in products]
        
        if category_filter:
            product_dicts = [p for p in product_dicts if p.get('category') == category_filter]
        
        semantic_search.index_products(product_dicts)
        results = semantic_search.search(query, top_k=top_k)
        
        response_data = {
            "query": query,
            "results": [
                {
                    "product": product,
                    "similarity_score": round(float(score), 4)
                }
                for product, score in results
            ],
            "total_results": len(results)
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def find_similar_products(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id", "").strip()
        top_k = min(int(data.get("top_k", 5)), 20)
        category_ids = data.get("category_ids", None)
        
        if not product_id:
            return JsonResponse({"error": "Product ID is required"}, status=400)
        
        products, _ = product_service.list_products(page=1, page_size=1000, category_ids=category_ids)
        product_dicts = [_product_to_dict(p) for p in products]
        
        semantic_search.index_products(product_dicts)
        results = semantic_search.find_similar_products(product_id, top_k=top_k)
        
        response_data = {
            "product_id": product_id,
            "similar_products": [
                {
                    "product": product,
                    "similarity_score": round(float(score), 4)
                }
                for product, score in results
            ],
            "total_results": len(results)
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def hybrid_search(request):
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        semantic_weight = float(data.get("semantic_weight", 0.7))
        keyword_weight = float(data.get("keyword_weight", 0.3))
        top_k = min(int(data.get("top_k", 10)), 50)
        category_ids = data.get("category_ids", None)
        
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)
        
        products, _ = product_service.list_products(page=1, page_size=1000, category_ids=category_ids)
        product_dicts = [_product_to_dict(p) for p in products]
        
        query_lower = query.lower()
        keyword_scores = {}
        for p in product_dicts:
            score = 0
            text = f"{p.get('name', '')} {p.get('description', '')} {p.get('category', '')}".lower()
            if query_lower in text:
                score = 1.0
                if query_lower in p.get('name', '').lower():
                    score = 1.5
            keyword_scores[p.get('id')] = score
        
        max_keyword = max(keyword_scores.values()) if keyword_scores else 1
        for pid in keyword_scores:
            keyword_scores[pid] = keyword_scores[pid] / max_keyword if max_keyword > 0 else 0
        
        semantic_search.index_products(product_dicts)
        semantic_results = semantic_search.search(query, top_k=len(product_dicts))
        
        combined_scores = {}
        for product, sem_score in semantic_results:
            pid = product.get('id')
            kw_score = keyword_scores.get(pid, 0)
            combined_scores[pid] = {
                'product': product,
                'semantic_score': sem_score,
                'keyword_score': kw_score,
                'combined_score': (semantic_weight * sem_score) + (keyword_weight * kw_score)
            }
        
        for pid, kw_score in keyword_scores.items():
            if pid not in combined_scores and kw_score > 0:
                for p in product_dicts:
                    if p.get('id') == pid:
                        combined_scores[pid] = {
                            'product': p,
                            'semantic_score': 0,
                            'keyword_score': kw_score,
                            'combined_score': keyword_weight * kw_score
                        }
                        break
        
        sorted_results = sorted(combined_scores.values(), key=lambda x: x['combined_score'], reverse=True)
        
        response_data = {
            "query": query,
            "semantic_weight": semantic_weight,
            "keyword_weight": keyword_weight,
            "results": [
                {
                    "product": r['product'],
                    "semantic_score": round(float(r['semantic_score']), 4),
                    "keyword_score": round(float(r['keyword_score']), 4),
                    "combined_score": round(float(r['combined_score']), 4)
                }
                for r in sorted_results[:top_k]
            ],
            "total_results": len(sorted_results)
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({"error": "An error occurred while processing your search request. Please try again."}, status=500)
