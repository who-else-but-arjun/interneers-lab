import csv
import io
import json
import urllib.parse
from decimal import Decimal
from typing import Optional, Dict, Any, List

from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from django_app.domain import product_service, product_category_service, stock_event_service


LOW_STOCK_THRESHOLD = 5


def _parse_csv_row(row: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse a single CSV row into product data."""
    product_data: Dict[str, Any] = {}
    for raw_key, raw_value in row.items():
        normalized_key = (raw_key or "").strip().lower()
        if normalized_key in ("name", "description", "category", "brand"):
            product_data[normalized_key] = (raw_value or "").strip()
        elif normalized_key == "price":
            try:
                product_data[normalized_key] = float(raw_value) if raw_value else 0
            except (TypeError, ValueError):
                product_data[normalized_key] = 0
        elif normalized_key == "quantity":
            try:
                product_data[normalized_key] = int(raw_value) if raw_value else 0
            except (TypeError, ValueError):
                product_data[normalized_key] = 0
        elif normalized_key == "category_id" and raw_value:
            try:
                product_data[normalized_key] = str(int(raw_value)) if str(raw_value).isdigit() else str(raw_value).strip()
            except (TypeError, ValueError):
                continue
    return product_data if product_data else None


def _handle_csv_upload(request: HttpRequest) -> tuple[Optional[Dict[str, str]], Optional[str]]:
    """Handle CSV upload. Returns (form_errors, success_message)."""
    uploaded = request.FILES["csv_file"]
    try:
        content = uploaded.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return {"csv_file": "File must be UTF-8 encoded"}, None

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return {"csv_file": "CSV has no data rows"}, None

    items: List[Dict[str, Any]] = []
    for row in rows:
        parsed = _parse_csv_row(row)
        if parsed:
            items.append(parsed)

    if not items:
        return {"csv_file": "CSV did not contain any usable product rows"}, None

    created, bulk_errors = product_service.create_many(items)
    form_errors = None
    success_message = None

    if bulk_errors:
        form_errors = {
            "csv_file": f"Created {len(created)} products, but {len(bulk_errors)} rows had validation issues."
        }
    if created:
        success_message = f"Successfully created {len(created)} product{'' if len(created) == 1 else 's'} from CSV."

    return form_errors, success_message


def _handle_single_product_create(request: HttpRequest) -> tuple[Optional[Dict[str, str]], Optional[str]]:
    """Handle single product form submission. Returns (form_errors, success_message)."""
    data = {
        "name": request.POST.get("name", ""),
        "description": request.POST.get("description", ""),
        "category": request.POST.get("category", ""),
        "price": request.POST.get("price", ""),
        "brand": request.POST.get("brand", ""),
        "quantity": request.POST.get("quantity", ""),
    }
    product, errors = product_service.create(data)
    if errors:
        return errors, None
    return None, f'Created product "{product.name}".'


def _apply_filters(
    products: List,
    category_ids: List[str],
    brands: List[str],
    product_ids: List[str]
) -> List:
    """Apply filters to product list."""
    filtered = list(products)
    if category_ids:
        filtered = [p for p in filtered if p.category_id in category_ids]
    if brands:
        filtered = [p for p in filtered if p.brand in brands]
    if product_ids:
        filtered = [p for p in filtered if p.id in product_ids]
    return filtered


def _build_dashboard_context(
    products: List,
    products_all: List,
    categories: List,
    selected_category_ids: List[str],
    selected_brands: List[str],
    selected_product_ids: List[str],
    form_errors: Optional[Dict[str, str]],
    success_message: Optional[str],
    stock_events: List,
    stock_events_total: int,
    upcoming_events: List,
    stock_events_summary: dict
) -> Dict[str, Any]:
    """Build template context for dashboard."""
    brand_options = sorted({p.brand for p in products_all if p.brand})
    product_options = products_all

    total_quantity = sum(p.quantity for p in products)
    total_value = sum(Decimal(str(p.price or 0)) * Decimal(str(p.quantity or 0)) for p in products)
    low_stock_products = [p for p in products if (p.quantity or 0) <= LOW_STOCK_THRESHOLD]

    chart_labels = [p.name for p in products]
    chart_quantities = [p.quantity for p in products]

    return {
        "products": products,
        "total_products": len(products),
        "total_quantity": total_quantity,
        "total_value": total_value,
        "form_errors": form_errors,
        "success_message": success_message,
        "chart_labels_json": json.dumps(chart_labels),
        "chart_quantities_json": json.dumps(chart_quantities),
        "categories": categories,
        "selected_category_ids": selected_category_ids,
        "brand_options": brand_options,
        "selected_brands": selected_brands,
        "product_options": product_options,
        "selected_product_ids": selected_product_ids,
        "low_stock_products": low_stock_products,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        # Stock events context
        "stock_events": stock_events,
        "stock_events_total": stock_events_total,
        "upcoming_events": upcoming_events,
        "stock_events_summary": stock_events_summary,
    }


@csrf_protect
@require_http_methods(["GET", "POST"])
def inventory_dashboard(request: HttpRequest) -> HttpResponse:
    """
    HTML inventory dashboard:
    - Shows current products in a table
    - Allows creating a new product via a form
    - Allows bulk CSV upload of products
    - Supports filtering by product category
    - Renders a stock-level chart and low-stock alerts
    """
    form_errors: Optional[Dict[str, str]] = None
    success_message: Optional[str] = None

    # Selected filters from query params
    selected_category_ids = request.GET.getlist("category_id")
    selected_brands = request.GET.getlist("brand")
    selected_product_ids = request.GET.getlist("product_filter")

    # Handle POST requests
    if request.method == "POST":
        if request.FILES.get("csv_file"):
            form_errors, success_message = _handle_csv_upload(request)
        else:
            form_errors, success_message = _handle_single_product_create(request)

    # Fetch data and apply filters
    products_all, _ = product_service.list_products(page=1, page_size=200, category_ids=None)
    categories = product_category_service.list_all()

    products = _apply_filters(products_all, selected_category_ids, selected_brands, selected_product_ids)

    # Get stock events data
    stock_events, stock_events_total = stock_event_service.list_events(page=1, page_size=50)
    upcoming_events = stock_event_service.get_upcoming_events(days=30)
    stock_events_summary = stock_event_service.get_event_summary()

    context = _build_dashboard_context(
        products, products_all, categories,
        selected_category_ids, selected_brands, selected_product_ids,
        form_errors, success_message,
        [e.to_dict() for e in stock_events],
        stock_events_total,
        [e.to_dict() for e in upcoming_events[:10]],
        stock_events_summary
    )
    return render(request, "django_app/inventory_dashboard.html", context)


@csrf_protect
@require_http_methods(["POST"])
def ui_product_delete(request: HttpRequest, product_id: str) -> HttpResponse:
    """
    Delete a product from the HTML dashboard.
    """
    product_service.delete(product_id)
    return redirect("inventory_dashboard")


@csrf_protect
@require_http_methods(["POST"])
def ui_export_products(request: HttpRequest) -> HttpResponse:
    """
    Export a selected subset of products as CSV, based on IDs checked in the dashboard.
    """
    ids = request.POST.getlist("selected_product")
    if not ids:
        return redirect(f"/?toast_error={urllib.parse.quote('No products selected for export.')}")

    products: List = []
    for pid in ids:
        p = product_service.get_by_id(pid)
        if p:
            products.append(p)

    if not products:
        return redirect(f"/?toast_error={urllib.parse.quote('Selected products no longer exist.')}")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "name", "brand", "category", "category_id", "price", "quantity", "description"]
    )
    for p in products:
        writer.writerow(
            [
                p.id,
                p.name,
                p.brand,
                p.category,
                p.category_id or "",
                p.price,
                p.quantity,
                p.description,
            ]
        )

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory_export.csv"'
    return response
