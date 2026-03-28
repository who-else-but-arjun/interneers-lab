import json
from typing import Optional

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from django_app.domain import stock_event_service
from django_app.repository.stock_event_repository_mongo import MongoStockEventRepository


@method_decorator(csrf_exempt, name="dispatch")
class StockEventListView(View):
    """List and create stock events."""
    
    def get(self, request):
        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))
            status: Optional[str] = request.GET.get("status")
            priority: Optional[str] = request.GET.get("priority")
            event_type: Optional[str] = request.GET.get("event_type")
            
            events, total = stock_event_service.list_events(
                page=page,
                page_size=page_size,
                status=status,
                priority=priority,
                event_type=event_type,
            )
            
            return JsonResponse({
                "success": True,
                "events": [e.to_dict() for e in events],
                "total": total,
                "page": page,
                "page_size": page_size,
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            event, errors = stock_event_service.create(data)
            
            if errors:
                return JsonResponse({"success": False, "errors": errors}, status=400)
            
            return JsonResponse({
                "success": True,
                "event": event.to_dict() if event else None
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class StockEventDetailView(View):
    """Get, update, or delete a specific stock event."""
    
    def get(self, request, event_id):
        try:
            event = stock_event_service.get_by_id(event_id)
            if not event:
                return JsonResponse({"success": False, "error": "Event not found"}, status=404)
            return JsonResponse({"success": True, "event": event.to_dict()})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    def put(self, request, event_id):
        try:
            data = json.loads(request.body)
            event, errors = stock_event_service.update(event_id, data)
            
            if errors:
                return JsonResponse({"success": False, "errors": errors}, status=400)
            
            if not event:
                return JsonResponse({"success": False, "error": "Event not found"}, status=404)
            
            return JsonResponse({"success": True, "event": event.to_dict()})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    def delete(self, request, event_id):
        try:
            success = stock_event_service.delete(event_id)
            if not success:
                return JsonResponse({"success": False, "error": "Event not found"}, status=404)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def stock_event_summary(request):
    """Get summary statistics for stock events."""
    try:
        summary = stock_event_service.get_event_summary()
        return JsonResponse({"success": True, "summary": summary})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def upcoming_stock_events(request):
    """Get upcoming stock events within specified days."""
    try:
        days = int(request.GET.get("days", 30))
        events = stock_event_service.get_upcoming_events(days)
        return JsonResponse({
            "success": True,
            "events": [e.to_dict() for e in events],
            "days": days,
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_ai_event(request):
    """Generate stock events using AI with inventory context."""
    try:
        data = json.loads(request.body)
        user_prompt = data.get("prompt", "")
        product_list = data.get("product_list", [])
        
        event_dict, error = stock_event_service.generate_ai_event(
            user_prompt=user_prompt,
            product_list=product_list
        )
        
        if error:
            return JsonResponse({"success": False, "error": error}, status=500)
        
        return JsonResponse({
            "success": True,
            "event": event_dict,
        })
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def apply_stock_event(request, event_id):
    """Apply a stock event to inventory."""
    try:
        success, message = stock_event_service.apply_event_to_inventory(event_id)
        if success:
            return JsonResponse({"success": True, "message": message})
        else:
            return JsonResponse({"success": False, "error": message}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
