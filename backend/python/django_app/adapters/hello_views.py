import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django_app.domain.hello import get_greeting


def _get_name_from_request(request):
    if request.method == "GET":
        return request.GET.get("name", "").strip() or None
    try:
        body = json.loads(request.body.decode("utf-8"))
        return (body.get("name") or "").strip() or None
    except (json.JSONDecodeError, AttributeError):
        return None

# this is a View function
@require_http_methods(["GET", "POST"])
@csrf_exempt
def hello_name(request):
    name = _get_name_from_request(request)
    print(name)
    message = get_greeting(name or "")
    return JsonResponse({"message": message})
