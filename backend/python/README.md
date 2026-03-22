# Interneers Lab - Backend in Python

Welcome to the **Interneers Lab 2026** Python backend. This project provides:

- **Hello API** — `GET` / `POST` `/hello/` with `name` (query or JSON body)
- **Product APIs** — Full CRUD for products stored in MongoDB (create, list, get, update, delete, bulk create, bulk CSV)
- **ProductCategory APIs** — CRUD for categories, products by category, add/remove product from category
- **Hexagonal architecture** — Domain, service, repository, and adapters. See [ARCHITECTURE.md](ARCHITECTURE.md).

**Important:** Use the same email you shared during onboarding when configuring Git.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Running Services](#running-services)
4. [APIs](#apis)
5. [Testing](#testing)
6. [MongoDB](#mongodb)
7. [Further Reading](#further-reading)
8. [Commands Reference](#commands-reference)

---

## Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **virtualenv** — `pip install virtualenv` or `python -m venv venv`
- **Docker & Docker Compose** — For MongoDB ([Docker Desktop](https://www.docker.com/products/docker-desktop/))
- **Postman** or similar — For API testing
- **MongoDB Compass** (optional) — To inspect the database

Verify: `python --version`, `docker --version`, `docker compose version`

---

## Setup

```bash
cd backend/python
python -m venv venv
```

Activate:

```bash
# macOS/Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` includes Django, pymongo, and mongoengine.

---

## Running Services

### 1. Start MongoDB

```bash
cd backend/python
docker compose up -d
docker compose ps
```

MongoDB runs on `localhost:27019` (user: `root`, password: `example`).

### 2. Start Django

```bash
cd backend/python
python manage.py runserver 8001
```

Server: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

---

## APIs

### Hello

- **GET** `http://127.0.0.1:8001/hello/?name=YourName`
- **POST** `http://127.0.0.1:8001/hello/` — Body: `{"name": "YourName"}`

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | List products (`?page=1&page_size=10&category_ids=id1,id2`) |
| POST | `/products/` | Create product |
| POST | `/products/bulk/` | Bulk create (body: JSON array) |
| POST | `/products/bulk/csv/` | Bulk create from CSV (form field `file`) |
| GET | `/products/<id>/` | Get one product |
| PUT / PATCH | `/products/<id>/` | Update product |
| POST | `/products/<id>/category/` | Add product to category (body: `{"category_id": "..."}`) |
| DELETE | `/products/<id>/category/` | Remove product from category |
| DELETE | `/products/<id>/` | Delete product |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories/` | List all categories |
| POST | `/categories/` | Create category (body: `{"title": "...", "description": "..."}`) |
| GET | `/categories/<id>/` | Get one category |
| PUT / PATCH | `/categories/<id>/` | Update category |
| DELETE | `/categories/<id>/` | Delete category |
| GET | `/categories/<id>/products/` | List products in category (`?page=1&page_size=10`) |

Create example:

```json
{
  "name": "Widget",
  "description": "A useful widget",
  "category": "Tools",
  "price": 9.99,
  "brand": "Acme",
  "quantity": 100
}
```

Required: `name`, `brand`, `price` (> 0), `quantity` (≥ 0). Optional: `category_id` (ObjectId string).

---

## Testing

Use Postman or curl:

- **Hello:** GET `http://127.0.0.1:8001/hello/?name=Bob`
- **Create product:** POST `http://127.0.0.1:8001/products/` with JSON body
- **List products:** GET `http://127.0.0.1:8001/products/`

Django tests:

```bash
python manage.py test
```

---

## MongoDB

Connection string: `mongodb://root:example@localhost:27019/?authSource=admin`

Database: `inventory`, Collections: `products`, `product_categories`

Environment variables (optional): `MONGO_HOST`, `MONGO_PORT`, `MONGO_USER`, `MONGO_PASS`, `MONGO_DB`, `MONGO_AUTH_SOURCE`

---

## Further Reading

- [Django](https://docs.djangoproject.com/)
- [MongoDB](https://docs.mongodb.com/)
- [MongoEngine](https://docs.mongoengine.org/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Commands Reference

```bash
# Virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
.\venv\Scripts\activate           # Windows
deactivate

# Dependencies
pip install -r requirements.txt

# Django
python manage.py runserver 8001
python manage.py test

# MongoDB (Docker)
docker compose up -d
docker compose down
docker compose ps
```
