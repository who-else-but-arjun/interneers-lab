import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django_app.domain import product_service


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
def product_list(request):
    if request.method == "GET":
        try:
            page = max(1, int(request.GET.get("page", 1)))
            page_size = min(100, max(1, int(request.GET.get("page_size", 10))))
        except (TypeError, ValueError):
            page, page_size = 1, 10
        items, total = product_service.list_products(page=page, page_size=page_size)
        return JsonResponse(
            {
                "items": [p.to_dict() for p in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            },
            status=200,
        )
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    product, errors = product_service.create(body)
    if errors:
        return _error_response("Validation failed", details=errors, status=400)
    return JsonResponse(product.to_dict(), status=201)


@require_http_methods(["POST"])
@csrf_exempt
def product_bulk_create(request):
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    if not isinstance(body, list):
        return _error_response("Body must be a JSON array of product objects", status=400)
    created, errors = product_service.create_many(body)
    return JsonResponse(
        {
            "created": len(created),
            "items": [p.to_dict() for p in created],
            "errors": errors if errors else None,
        },
        status=201,
    )


@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@csrf_exempt
def product_detail(request, product_id):
    if request.method == "GET":
        product = product_service.get_by_id(product_id)
        if not product:
            return _error_response("Product not found", status=404)
        return JsonResponse(product.to_dict(), status=200)
    if request.method == "DELETE":
        if product_service.delete(product_id):
            return HttpResponse(status=204)
        return _error_response("Product not found", status=404)
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    product, errors = product_service.update(product_id, body)
    if errors:
        if errors.get("_error") == "Product not found":
            return _error_response("Product not found", status=404)
        return _error_response("Validation failed", details=errors, status=400)
    return JsonResponse(product.to_dict(), status=200)
