import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from django_app.domain.rag_service import rag_chat_with_tracing, generate_chat_title


@require_http_methods(["POST"])
@csrf_exempt
def generate_chat_title_endpoint(request):
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
        message = body.get("message", "").strip()

        if not message:
            return JsonResponse({"success": False, "error": "Please provide a message"}, status=400)

        return JsonResponse({"success": True, "title": generate_chat_title(message)})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def rag_chat_endpoint(request):
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
        message = body.get("message", "").strip()
        chat_history = body.get("chat_history", [])

        if not message:
            return JsonResponse({"success": False, "error": "Please provide a message"}, status=400)

        result = rag_chat_with_tracing(message, chat_history)

        langsmith_project = getattr(settings, "LANGSMITH_PROJECT", "inventory-rag")
        trace_url = (
            f"https://smith.langchain.com/o/default/projects/{langsmith_project}/traces/{result['trace_id']}"
            if result.get("trace_id") else None
        )

        return JsonResponse({
            "success":   True,
            "response":  result["response"],
            "message":   message,
            "trace_id":  result.get("trace_id"),
            "trace_url": trace_url,
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)