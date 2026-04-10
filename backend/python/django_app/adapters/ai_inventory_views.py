import json
from datetime import datetime
from typing import Optional
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from pydantic import BaseModel, Field, validator

from django_app.domain import product_service, product_category_service
from django_app.domain.ai_inventory_service import AIInventoryService
from django_app.repository.ai_inventory_chat_repository_mongo import AIInventoryChatRepositoryMongo


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


@csrf_protect
@require_http_methods(["GET"])
def ai_scenario_dashboard(request):
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
    try:
        body = json.loads(request.body)
        user_message = body.get("scenario_text", "").strip()
        max_count = min(int(body.get("count", 10)), 50)
        chat_history = body.get("chat_history", [])
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
    
    if not user_message:
        return JsonResponse({"success": False, "error": "Please enter a message"}, status=400)
    
    try:
        ai_response = AIInventoryService.process_ai_chat(user_message, max_count, chat_history)
        
        intent = ai_response.get("intent", "chat")
        
        if intent == "product_generation":
            products = ai_response.get("products", [])
            valid_products, invalid_count = _validate_products_list(products)
            
            return JsonResponse({
                "success": True,
                "intent": "product_generation",
                "scenario_text": user_message,
                "requested_count": max_count,
                "generated_count": len(valid_products),
                "saved_count": 0,
                "invalid_count": invalid_count,
                "products": valid_products,
                "chat_message": ai_response.get("message", f"I have generated {len(valid_products)} products for you!")
            })
        else:
            return JsonResponse({
                "success": True,
                "intent": "chat",
                "scenario_text": user_message,
                "chat_message": ai_response.get("message", "I'm here to help with your inventory!"),
                "products": [],
                "generated_count": 0,
                "saved_count": 0,
                "invalid_count": 0
            })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)




def _validate_products_list(products_list):
    valid_products = []
    invalid_count = 0
    
    if not isinstance(products_list, list):
        return [], 0
    
    for prod_data in products_list:
        try:
            prod_data['created_at'] = datetime.utcnow().isoformat()
            prod_data['updated_at'] = datetime.utcnow().isoformat()
            product = ProductModel(**prod_data)
            valid_products.append(product.dict())
        except:
            invalid_count += 1
    
    return valid_products, invalid_count




class AIInventoryChatListView(View):
    def get(self, request):
        session_id = request.session.session_key or request.COOKIES.get('sessionid', 'anonymous')
        chats = AIInventoryChatRepositoryMongo.get_chats_by_session(session_id)
        return JsonResponse({"chats": chats})
    
    def post(self, request):
        try:
            body = json.loads(request.body)
            session_id = request.session.session_key or request.COOKIES.get('sessionid', 'anonymous')
            title = body.get('title', 'New Chat')
            
            chat = AIInventoryChatRepositoryMongo.create_chat(session_id, title)
            return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class AIInventoryChatDetailView(View):
    def get(self, request, chat_id):
        session_id = request.session.session_key or request.COOKIES.get('sessionid', 'anonymous')
        chat = AIInventoryChatRepositoryMongo.get_chat(chat_id, session_id)
        if chat:
            return JsonResponse(chat)
        return JsonResponse({"error": "Chat not found"}, status=404)
    
    def delete(self, request, chat_id):
        session_id = request.session.session_key or request.COOKIES.get('sessionid', 'anonymous')
        success = AIInventoryChatRepositoryMongo.delete_chat(chat_id, session_id)
        if success:
            return JsonResponse({"success": True})
        return JsonResponse({"error": "Chat not found"}, status=404)


class AIInventoryChatSyncView(View):
    def post(self, request):
        try:
            body = json.loads(request.body)
            session_id = request.session.session_key or request.COOKIES.get('sessionid', 'anonymous')
            chat_id = body.get('chat_id')
            messages = body.get('messages', [])
            title = body.get('title')
            
            if chat_id:
                success = AIInventoryChatRepositoryMongo.update_chat(chat_id, session_id, messages, title)
                if success:
                    return JsonResponse({"success": True, "chat_id": chat_id})
                return JsonResponse({"error": "Chat not found"}, status=404)
            else:
                chat = AIInventoryChatRepositoryMongo.create_chat(session_id, title or "New Chat")
                if messages:
                    AIInventoryChatRepositoryMongo.update_chat(chat['id'], session_id, messages, title)
                    chat['messages'] = messages
                return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
