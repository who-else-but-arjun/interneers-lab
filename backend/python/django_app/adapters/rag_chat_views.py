import json
import traceback
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..repository.rag_chat_repository_mongo import RagChatRepositoryMongo


def get_session_id(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


@method_decorator(csrf_exempt, name="dispatch")
class RagChatListView(View):

    def get(self, request):
        try:
            chats = RagChatRepositoryMongo.get_chats_by_session(get_session_id(request))
            return JsonResponse({"success": True, "chats": chats})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def post(self, request):
        try:
            data  = json.loads(request.body)
            title = data.get("title", "New Chat")
            chat  = RagChatRepositoryMongo.create_chat(get_session_id(request), title)
            return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class RagChatDetailView(View):

    def get(self, request, chat_id):
        try:
            chat = RagChatRepositoryMongo.get_chat(chat_id, get_session_id(request))
            if not chat:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True, "chat": chat})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def put(self, request, chat_id):
        try:
            data     = json.loads(request.body)
            success  = RagChatRepositoryMongo.update_chat(
                chat_id, get_session_id(request),
                data.get("messages", []), data.get("title"),
            )
            if not success:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def delete(self, request, chat_id):
        try:
            success = RagChatRepositoryMongo.delete_chat(chat_id, get_session_id(request))
            if not success:
                return JsonResponse({"success": False, "error": "Chat not found"}, status=404)
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Delete error for chat {chat_id}: {e}\n{traceback.format_exc()}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class RagChatSyncView(View):

    def post(self, request):
        try:
            data         = json.loads(request.body)
            session_id   = get_session_id(request)
            synced_count = 0

            for chat in data.get("chats", []):
                chat_id  = chat.get("id")
                messages = chat.get("messages", [])
                title    = chat.get("title", "New Chat")

                existing = RagChatRepositoryMongo.get_chat(chat_id, session_id)
                if existing:
                    RagChatRepositoryMongo.update_chat(chat_id, session_id, messages, title)
                else:
                    new_chat = RagChatRepositoryMongo.create_chat(session_id, title)
                    RagChatRepositoryMongo.update_chat(new_chat["id"], session_id, messages, title)

                synced_count += 1

            return JsonResponse({"success": True, "synced_count": synced_count})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"Sync error: {e}\n{traceback.format_exc()}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)