from __future__ import annotations

import asyncio
import json
import threading
import queue

from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from django_app.domain.quote_agent_service import QuoteAgentService
from django_app.repository.quote_agent_chat_repository_mongo import (
    QuoteAgentChatRepositoryMongo,
)

_service: QuoteAgentService = None

def _get_service() -> QuoteAgentService:
    global _service
    if _service is None:
        _service = QuoteAgentService()
    return _service

def _get_session_id(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

@method_decorator(csrf_exempt, name="dispatch")
class QuoteAgentChatListView(View):

    def get(self, request):
        try:
            chats = QuoteAgentChatRepositoryMongo.get_chats_by_session(
                _get_session_id(request)
            )
            return JsonResponse({"success": True, "chats": chats})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def post(self, request):
        try:
            data  = json.loads(request.body)
            title = data.get("title", "New Chat")
            chat  = QuoteAgentChatRepositoryMongo.create_chat(
                _get_session_id(request), title
            )
            return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

@method_decorator(csrf_exempt, name="dispatch")
class QuoteAgentChatDetailView(View):

    def get(self, request, chat_id):
        try:
            chat = QuoteAgentChatRepositoryMongo.get_chat(
                chat_id, _get_session_id(request)
            )
            if not chat:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def put(self, request, chat_id):
        try:
            data    = json.loads(request.body)
            success = QuoteAgentChatRepositoryMongo.update_chat(
                chat_id,
                _get_session_id(request),
                data.get("messages", []),
                data.get("title"),
            )
            if not success:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def delete(self, request, chat_id):
        try:
            success = QuoteAgentChatRepositoryMongo.delete_chat(
                chat_id, _get_session_id(request)
            )
            if not success:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

@method_decorator(csrf_exempt, name="dispatch")
class QuoteAgentChatSyncView(View):

    def post(self, request):
        try:
            data       = json.loads(request.body)
            session_id = _get_session_id(request)
            if "chats" not in data and ("messages" in data or "title" in data):
                chat_id    = data.get("chat_id")
                messages   = data.get("messages")
                title      = data.get("title")
                title_only = messages is None

                if chat_id:
                    if title_only:
                        existing = QuoteAgentChatRepositoryMongo.get_chat(chat_id, session_id)
                        if existing and title:
                            QuoteAgentChatRepositoryMongo.update_chat(
                                chat_id, session_id, existing["messages"], title
                            )
                        return JsonResponse({"success": True, "chat_id": chat_id})
                    success = QuoteAgentChatRepositoryMongo.update_chat(
                        chat_id, session_id, messages or [], title
                    )
                    if success:
                        return JsonResponse({"success": True, "chat_id": chat_id})
                    return JsonResponse({"error": "Chat not found"}, status=404)
                else:
                    chat = QuoteAgentChatRepositoryMongo.create_chat(
                        session_id, title or "New Chat"
                    )
                    if messages:
                        QuoteAgentChatRepositoryMongo.update_chat(
                            chat["id"], session_id, messages, title
                        )
                        chat["messages"] = messages
                    return JsonResponse({"success": True, "chat": chat})
            synced_count = 0
            for chat in data.get("chats", []):
                chat_id  = chat.get("id")
                messages = chat.get("messages", [])
                title    = chat.get("title", "New Chat")

                existing = QuoteAgentChatRepositoryMongo.get_chat(chat_id, session_id)
                if existing:
                    QuoteAgentChatRepositoryMongo.update_chat(
                        chat_id, session_id, messages, title
                    )
                else:
                    new_chat = QuoteAgentChatRepositoryMongo.create_chat(session_id, title)
                    QuoteAgentChatRepositoryMongo.update_chat(
                        new_chat["id"], session_id, messages, title
                    )
                synced_count += 1

            return JsonResponse({"success": True, "synced_count": synced_count})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def agent_chat(request):

    try:
        data         = json.loads(request.body)
        user_request = data.get("message", "").strip()
        chat_history = data.get("chat_history", [])
        chat_id      = data.get("chat_id")
        title        = data.get("title")
        session_id   = _get_session_id(request)

        if not user_request:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        result = _get_service().process_request(user_request, chat_history)
        updated_messages = list(chat_history) + [
            {"role": "user",      "content": user_request},
            {"role": "assistant", "content": result["response"]},
        ]
        saved_chat_id = _upsert_chat(session_id, chat_id, updated_messages, title)

        return JsonResponse({
            "status":     "success",
            "response":   result["response"],
            "tool_calls": result.get("tool_calls", []),
            "quote":      result.get("quote"),
            "trace_id":   result.get("trace_id"),
            "chat_id":    saved_chat_id,
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def agent_chat_stream(request):

    try:
        data         = json.loads(request.body)
        user_request = data.get("message", "").strip()
        chat_history = data.get("chat_history", [])
        chat_id      = data.get("chat_id")
        title        = data.get("title")
        session_id   = _get_session_id(request)

        if not user_request:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        event_queue: queue.Queue = queue.Queue()
        _SENTINEL = object()

        def run_async():
            async def _produce():
                try:
                    async for event in _get_service().aprocess_request(
                        user_request, chat_history
                    ):
                        event_queue.put(f"data: {json.dumps(event)}\n\n")
                        if event.get("type") == "result":
                            payload          = event.get("data", {})
                            assistant_text   = payload.get("response", "")
                            updated_messages = list(chat_history) + [
                                {"role": "user",      "content": user_request},
                                {"role": "assistant", "content": assistant_text},
                            ]
                            saved_id = _upsert_chat(
                                session_id, chat_id, updated_messages, title
                            )
                            event_queue.put(
                                f"data: {json.dumps({'type': 'saved', 'chat_id': saved_id})}\n\n"
                            )

                except Exception as e:
                    event_queue.put(
                        f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                    )
                finally:
                    event_queue.put(_SENTINEL)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_produce())
            finally:
                loop.close()

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

        def event_stream():
            while True:
                item = event_queue.get()
                if item is _SENTINEL:
                    break
                yield item

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"]     = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def search_products_for_quote(request):
    try:
        data  = json.loads(request.body)
        query = data.get("query", "").strip().lower()

        if not query:
            return JsonResponse({"error": "Query cannot be empty"}, status=400)

        from django_app.domain.product_service import list_products
        products, _ = list_products(page=1, page_size=100)

        results = [
            {
                "id":       str(p.id),
                "name":     p.name,
                "brand":    p.brand,
                "price":    float(p.price),
                "quantity": int(p.quantity),
                "category": p.category,
            }
            for p in products
            if query in p.name.lower() or query in p.brand.lower()
        ]

        return JsonResponse({"status": "success", "results": results[:10]})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def agent_status(request):
    service         = _get_service()
    tools_available = [tool.name for tool in service.tools]
    return JsonResponse({
        "status":           "active",
        "tools_available":  tools_available,
        "rag_integrated":   True,
        "max_discount_pct": 20,
    })

def _upsert_chat(
    session_id: str,
    chat_id: str | None,
    messages: list,
    title: str | None,
) -> str:

    if chat_id:
        QuoteAgentChatRepositoryMongo.update_chat(
            chat_id, session_id, messages, title
        )
        return chat_id
    chat = QuoteAgentChatRepositoryMongo.create_chat(
        session_id, title or "New Chat"
    )
    QuoteAgentChatRepositoryMongo.update_chat(
        chat["id"], session_id, messages, title
    )
    return chat["id"]