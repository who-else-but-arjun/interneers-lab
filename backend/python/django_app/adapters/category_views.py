import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django_app.domain import product_category_service, product_service


def _parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, AttributeError):
        return None


def _error_response(message: str, details: dict = None, status: int = 400):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return JsonResponse(payload, status=status)


@require_http_methods(["GET", "POST"])
@csrf_exempt
def category_list(request):
    if request.method == "GET":
        items = product_category_service.list_all()
        return JsonResponse({"items": [c.to_dict() for c in items]}, status=200)
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    category, errors = product_category_service.create(body)
    if errors:
        return _error_response("Validation failed", details=errors, status=400)
    return JsonResponse(category.to_dict(), status=201)


@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@csrf_exempt
def category_detail(request, category_id):
    if request.method == "GET":
        category = product_category_service.get_by_id(category_id)
        if not category:
            return _error_response("Category not found", status=404)
        return JsonResponse(category.to_dict(), status=200)
    if request.method == "DELETE":
        if product_category_service.delete(category_id):
            return HttpResponse(status=204)
        return _error_response("Category not found", status=404)
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    category, errors = product_category_service.update(category_id, body)
    if errors:
        if errors.get("_error") == "Category not found":
            return _error_response("Category not found", status=404)
        return _error_response("Validation failed", details=errors, status=400)
    return JsonResponse(category.to_dict(), status=200)


@require_http_methods(["GET"])
@csrf_exempt
def category_products(request, category_id):
    try:
        page = max(1, int(request.GET.get("page", 1)))
        page_size = min(100, max(1, int(request.GET.get("page_size", 10))))
    except (TypeError, ValueError):
        page, page_size = 1, 10
    category = product_category_service.get_by_id(category_id)
    if not category:
        return _error_response("Category not found", status=404)
    items, total = product_service.list_products(
        page=page, page_size=page_size, category_ids=[category_id]
    )
    return JsonResponse(
        {
            "items": [p.to_dict() for p in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        status=200,
    )
