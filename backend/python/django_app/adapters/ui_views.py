import csv
import io
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from django_app.domain import product_service, product_category_service
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import google.generativeai as genai
import os

GEMINI_API_KEY = "AIzaSyDQJRDSgJllCXNp3QPvWlTkcVvetw1DDnI"
genai.configure(api_key=GEMINI_API_KEY)


class ProductModel(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    brand: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)
    category_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('quantity')
    def quantity_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Quantity must be 0 or greater')
        return int(v)


SCENARIO_PROMPTS = {
    "Holiday Rush": "Generate popular holiday gift items like toys, games, and festive products with HIGH stock levels (200-500 units) to prepare for holiday demand",
    "Back to School": "Generate educational supplies, learning toys, school accessories with MODERATE stock levels (100-300 units)",
    "Summer Sale": "Generate outdoor toys, water games, sports equipment with HIGH stock levels (150-400 units) for summer season",
    "Clearance": "Generate various toy categories with LOW stock levels (10-50 units) as clearance items",
    "New Arrivals": "Generate trending new toys, tech gadgets for kids, innovative games with MODERATE stock levels (80-200 units)",
    "Standard Inventory": "Generate a balanced mix of toy categories with standard stock levels (50-200 units)"
}


@csrf_protect
@require_http_methods(["GET", "POST"])
def inventory_dashboard(request):
    """
    HTML inventory dashboard:
    - Shows current products in a table
    - Allows creating a new product via a form
    - Allows bulk CSV upload of products
    - Supports filtering by product category
    - Renders a stock-level chart and low-stock alerts
    """
    form_errors: dict[str, str] | None = None
    success_message: str | None = None

    # Selected filters from query params (all based on current data, not hardcoded).
    selected_category_ids = request.GET.getlist("category_id")
    selected_brands = request.GET.getlist("brand")
    selected_product_ids = request.GET.getlist("product_filter")

    # Global low-stock threshold used for highlighting.
    LOW_STOCK_THRESHOLD = 5

    if request.method == "POST":
        # Bulk CSV upload path
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
                                    # Ignore invalid category_id in CSV
                                    continue
                        if d:
                            items.append(d)
                    if not items:
                        form_errors = {"csv_file": "CSV did not contain any usable product rows"}
                    else:
                        created, bulk_errors = product_service.create_many(items)
                        if bulk_errors:
                            # Surface a concise summary; detailed errors stay server-side.
                            form_errors = {
                                "csv_file": f"Created {len(created)} products, "
                                f"but {len(bulk_errors)} rows had validation issues."
                            }
                        if created:
                            success_message = (
                                f"Successfully created {len(created)} product"
                                f"{'' if len(created) == 1 else 's'} from CSV."
                            )
        # Single product create path
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
                success_message = f"Created product “{product.name}”."

    # Fetch all products and derive dynamic filter options from current data.
    products_all, total_all = product_service.list_products(
        page=1,
        page_size=200,
        category_ids=None,
    )
    categories = product_category_service.list_all()

    # Compute dynamic lists for filters.
    brand_options = sorted({p.brand for p in products_all if p.brand})
    product_options = products_all

    # Apply filters in-memory on the current dataset.
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
    }
    return render(request, "django_app/inventory_dashboard.html", context)


@csrf_protect
@require_http_methods(["POST"])
def ui_product_delete(request, product_id: str):
    """
    Delete a product from the HTML dashboard.
    """
    product_service.delete(product_id)
    return redirect("inventory_dashboard")


@csrf_protect
@require_http_methods(["POST"])
def ui_export_products(request):
    """
    Export a selected subset of products as CSV, based on IDs checked in the dashboard.
    """
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


@csrf_protect
@require_http_methods(["GET"])
def ai_scenario_dashboard(request):
    """
    AI Chatbot-style Dashboard:
    - Users type custom scenarios in natural language
    - AI generates products based on their custom description
    """
    categories = product_category_service.list_all()
    summary = _get_inventory_summary()
    
    context = {
        "categories": categories,
        "current_inventory": summary,
    }
    return render(request, "django_app/ai_scenario_dashboard.html", context)


@csrf_protect
@require_http_methods(["POST"])
def ai_generate_products(request):
    """
    API endpoint to generate products using Gemini AI based on custom user scenario text.
    """
    try:
        body = json.loads(request.body)
        scenario_text = body.get("scenario_text", "").strip()
        count = min(int(body.get("count", 10)), 50)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
    
    if not scenario_text:
        return JsonResponse({"success": False, "error": "Please describe what products you want to generate"}, status=400)
    
    try:
        raw_response = _generate_products_with_custom_scenario(scenario_text, count)
        valid_products, invalid_count = _clean_and_validate_products(raw_response)
        
        return JsonResponse({
            "success": True,
            "scenario_text": scenario_text,
            "requested_count": count,
            "generated_count": len(valid_products),
            "saved_count": 0,
            "invalid_count": invalid_count,
            "products": valid_products
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def _generate_products_with_custom_scenario(scenario_text, count=10):
    """Generate products using Gemini API based on custom user scenario text."""
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""Generate {count} products for a toy store inventory based on this request:
"{scenario_text}"

Return ONLY a valid JSON array with no markdown formatting, no explanation text.

Each product must have these exact fields:
- name: string (product name)
- description: string (brief description)
- category: string (product category)
- price: float (price in USD, between 5.0 and 200.0)
- brand: string (brand name)
- quantity: integer (stock quantity)

Output format: [{{"name": "...", "description": "...", "category": "...", "price": 29.99, "brand": "...", "quantity": 100}}, ...]"""
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4096
        )
    )
    
    return response.text


def _clean_and_validate_products(json_text):
    """Clean JSON response and validate products using Pydantic."""
    text = json_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        raw_products = json.loads(text)
    except json.JSONDecodeError:
        return [], 0
    
    valid_products = []
    invalid_count = 0
    
    for prod_data in raw_products:
        try:
            prod_data['created_at'] = datetime.utcnow().isoformat()
            prod_data['updated_at'] = datetime.utcnow().isoformat()
            product = ProductModel(**prod_data)
            valid_products.append(product.dict())
        except:
            invalid_count += 1
    
    return valid_products, invalid_count


def _save_products_to_service(products):
    """Save validated products to the product service."""
    created_count = 0
    for prod in products:
        data = {
            "name": prod['name'],
            "description": prod['description'],
            "category": prod['category'],
            "price": prod['price'],
            "brand": prod['brand'],
            "quantity": prod['quantity'],
        }
        product, errors = product_service.create(data)
        if not errors:
            created_count += 1
    return created_count


def _get_inventory_summary():
    """Get current inventory summary."""
    products, _ = product_service.list_products(page=1, page_size=1000, category_ids=None)
    total_value = sum((p.price or 0) * (p.quantity or 0) for p in products)
    low_stock = sum(1 for p in products if (p.quantity or 0) < 50)
    
    categories = {}
    for p in products:
        categories[p.category] = categories.get(p.category, 0) + 1
    
    return {
        "total_products": len(products),
        "total_value": total_value,
        "low_stock_count": low_stock,
        "categories": categories
    }
