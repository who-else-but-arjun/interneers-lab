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


def _parse_category_ids(param: str) -> list[str] | None:
    if not param or not param.strip():
        return None
    ids = [x.strip() for x in param.split(",") if x.strip()]
    return ids if ids else None


def _product_to_dict(product):
    """Convert a product object to a dictionary."""
    return product.to_dict()


@require_http_methods(["GET", "POST"])
@csrf_exempt
def product_list(request):
    if request.method == "GET":
        try:
            page = max(1, int(request.GET.get("page", 1)))
            page_size = min(100, max(1, int(request.GET.get("page_size", 5))))
        except (TypeError, ValueError):
            page, page_size = 1, 5
        category_ids = _parse_category_ids(request.GET.get("category_ids", ""))
        items, total = product_service.list_products(
            page=page, page_size=page_size, category_ids=category_ids
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


@require_http_methods(["POST", "DELETE"])
@csrf_exempt
def product_add_to_category(request, product_id):
    if request.method == "DELETE":
        product, errors = product_service.update(product_id, {"category_id": None})
        if errors:
            if errors.get("_error") == "Product not found":
                return _error_response("Product not found", status=404)
            return _error_response("Validation failed", details=errors, status=400)
        return JsonResponse(product.to_dict(), status=200)
    body = _parse_json_body(request)
    if body is None:
        return _error_response("Invalid JSON body", status=400)
    category_id = body.get("category_id")
    if not category_id:
        return _error_response("category_id is required", status=400)
    product, errors = product_service.update(
        product_id, {"category_id": str(category_id)}
    )
    if errors:
        if errors.get("_error") == "Product not found":
            return _error_response("Product not found", status=404)
        return _error_response("Validation failed", details=errors, status=400)
    return JsonResponse(product.to_dict(), status=200)


@require_http_methods(["POST"])
@csrf_exempt
def product_bulk_csv(request):
    import csv
    import io
    if not request.FILES or "file" not in request.FILES:
        return _error_response("No file uploaded; use form field 'file'", status=400)
    uploaded = request.FILES["file"]
    try:
        content = uploaded.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return _error_response("File must be UTF-8 encoded", status=400)
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return _error_response("CSV has no data rows", status=400)
    items = []
    for row in rows:
        d = {}
        for k, v in row.items():
            kk = k.strip().lower()
            if kk in ("name", "description", "category", "brand"):
                d[kk] = (v or "").strip()
            elif kk == "price":
                try:
                    d[kk] = float(v) if v else 0
                except (TypeError, ValueError):
                    d[kk] = 0
            elif kk == "quantity":
                try:
                    d[kk] = int(v) if v else 0
                except (TypeError, ValueError):
                    d[kk] = 0
            elif kk == "category_id" and v:
                try:
                    d[kk] = str(int(v)) if str(v).isdigit() else str(v).strip()
                except (TypeError, ValueError):
                    pass
        items.append(d)
    created, errors = product_service.create_many(items)
    return JsonResponse(
        {
            "created": len(created),
            "items": [p.to_dict() for p in created],
            "errors": errors if errors else None,
        },
        status=201,
    )
