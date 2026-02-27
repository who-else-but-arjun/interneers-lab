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

## Flow for Product APIs (Week 2 + Week 3)

| Layer        | Location                    | Role |
|-------------|-----------------------------|------|
| Controller  | `django_app/adapters/`      | Thin HTTP layer: parses request, calls service, returns JSON. |
| Service     | `django_app/domain/product_service.py` | Business logic and validation; uses repository for persistence. |
| Repository  | `django_app/repository/`     | Data access: implements `ProductRepository`; Mongo implementation uses MongoEngine and MongoDB. |
| Persistence | `django_app/repository/product_document.py` | MongoEngine document (ProductDocument) with created_at, updated_at. |

- **GET/POST** `/products/` and **GET/PUT/PATCH/DELETE** `/products/<id>/`: adapter → ProductService → ProductRepository (Mongo). List supports `?category_ids=id1,id2` filter. API responses include `created_at`, `updated_at`, `category_id`.
- **ProductCategory** (Week 4): `ProductCategoryDocument` (title, description). ProductDocument has optional `category_id` (ObjectId reference). ProductCategoryService + ProductCategoryRepository. CRUD at `/categories/`, products by category at `/categories/<id>/products/`, add/remove product from category via POST/DELETE `/products/<id>/category/`.
- **Bulk CSV**: POST `/products/bulk/csv/` with multipart form file. **Seed**: On startup, creates Food, Kitchen Essentials, Electronics categories if none exist. **Migration**: Products without `category_id` are assigned to "Uncategorized" category. **Brand** is now required for product create.


created new branch