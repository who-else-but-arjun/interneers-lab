import csv
import io
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from django_app.domain import product_service, product_category_service, stock_event_service


@csrf_protect
@require_http_methods(["GET", "POST"])
def inventory_dashboard(request):
    form_errors: dict[str, str] | None = None
    success_message: str | None = None

    selected_category_ids = request.GET.getlist("category_id")
    selected_brands = request.GET.getlist("brand")
    selected_product_ids = request.GET.getlist("product_filter")

    LOW_STOCK_THRESHOLD = 5

    if request.method == "POST":
        if request.FILES.get("csv_file"):
            uploaded = request.FILES["csv_file"]
            try:
                content = uploaded.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                form_errors = {"csv_file": "File must be UTF-8 encoded"}
            else:
                reader = csv.DictReader(io.StringIO(content))
                rows = list(reader)
                if not rows:
                    form_errors = {"csv_file": "CSV has no data rows"}
                else:
                    items: list[dict] = []
                    for row in rows:
                        d: dict[str, object] = {}
                        for k, v in row.items():
                            kk = (k or "").strip().lower()
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
                                    continue
                        if d:
                            items.append(d)
                    if not items:
                        form_errors = {"csv_file": "CSV did not contain any usable product rows"}
                    else:
                        created, bulk_errors = product_service.create_many(items)
                        if bulk_errors:
                            form_errors = {
                                "csv_file": f"Created {len(created)} products, "
                                f"but {len(bulk_errors)} rows had validation issues."
                            }
                        if created:
                            success_message = (
                                f"Successfully created {len(created)} product"
                                f"{'' if len(created) == 1 else 's'} from CSV."
                            )
        else:
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
                form_errors = errors
            else:
                success_message = f"Created product '{product.name}'."

    products_all, total_all = product_service.list_products(
        page=1,
        page_size=200,
        category_ids=None,
    )
    categories = product_category_service.list_all()

    brand_options = sorted({p.brand for p in products_all if p.brand})
    product_options = products_all

    products = list(products_all)
    if selected_category_ids:
        products = [
            p for p in products
            if p.category_id in selected_category_ids
        ]
    if selected_brands:
        products = [
            p for p in products
            if p.brand in selected_brands
        ]
    if selected_product_ids:
        products = [
            p for p in products
            if p.id in selected_product_ids
        ]

    total_quantity = sum(p.quantity for p in products)
    total_value = sum((p.price or 0) * (p.quantity or 0) for p in products)

    low_stock_products = [p for p in products if (p.quantity or 0) <= LOW_STOCK_THRESHOLD]

    chart_labels = [p.name for p in products]
    chart_quantities = [p.quantity for p in products]

    # Get stock events data
    stock_events, stock_events_total = stock_event_service.list_events(page=1, page_size=50)
    upcoming_events = stock_event_service.get_upcoming_events(days=30)
    stock_events_summary = stock_event_service.get_event_summary()

    context = {
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
        "stock_events": [e.to_dict() for e in stock_events],
        "stock_events_total": stock_events_total,
        "upcoming_events": [e.to_dict() for e in upcoming_events[:10]],  # Top 10 upcoming
        "stock_events_summary": stock_events_summary,
    }
    return render(request, "django_app/inventory_dashboard.html", context)


@csrf_protect
@require_http_methods(["POST"])
def ui_product_delete(request, product_id: str):
    product_service.delete(product_id)
    return redirect("inventory_dashboard")


@csrf_protect
@require_http_methods(["POST"])
def ui_export_products(request):
    ids = request.POST.getlist("selected_product")
    if not ids:
        return redirect("inventory_dashboard")

    products: list = []
    for pid in ids:
        p = product_service.get_by_id(pid)
        if p:
            products.append(p)

    if not products:
        return redirect("inventory_dashboard")

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
