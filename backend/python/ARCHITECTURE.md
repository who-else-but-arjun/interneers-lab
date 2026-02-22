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

## Flow for Product APIs (Week 2)

- **GET/POST** `/products/` → `product_list`: GET returns paginated list (query params `page`, `page_size`); POST creates a product (JSON body). Validates input and returns 400 with `error` and `details` on failure.
- **GET/PUT/PATCH/DELETE** `/products/<id>/` → `product_detail`: get one, update, or delete. Domain holds in-memory store; all validations and business rules live in `domain/product.py` and `domain/product_service.py`.
