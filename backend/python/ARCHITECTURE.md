# Hexagonal architecture – Week 1 layering

This project uses a simple hexagonal (ports & adapters) layout so HTTP is just one way to trigger the same logic.

## Layers

| Layer      | Location              | Role |
|-----------|------------------------|------|
| Domain    | `django_app/domain/`   | Pure business logic. No Django or HTTP. Inputs/outputs are plain types. |
| Adapters  | `django_app/adapters/` | Translate external world (e.g. HTTP request/response) into calls to the domain and back. |
| URLs      | `django_app/urls.py`   | Maps HTTP paths to adapter views. |

## Flow for `GET/POST /hello/`

1. **Request** hits Django and is routed to `hello_name` in `adapters/hello_views.py`.
2. **Adapter** reads `name` from query (GET) or JSON body (POST), prints it, then calls `get_greeting(name)` in `domain/hello.py`.
3. **Domain** returns a greeting string (e.g. `"Hello, World!"`).
4. **Adapter** wraps it in `JsonResponse({"message": ...})` and returns the HTTP response.

Domain stays independent of HTTP; only adapters know about `request` and `JsonResponse`.
