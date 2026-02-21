<<<<<<< HEAD
# Interneers Lab

Welcome to the **Interneers Lab** repository! This serves as a minimal starter kit for learning and experimenting with:
- **Django** (Python)
- **Golang** (Go)
- **React**  (with TypeScript)
- **MongoDB** (via Docker Compose)
- Development environment in **VSCode** (recommended)

**Important:** Use the **same email** you shared during onboarding when configuring Git and related tools. That ensures consistency across all internal systems.

### Project structure

```
backend/
  go/          # Golang backend (see backend/go/README.md)
  python/      # Django (Python) backend (see backend/python/README.md)
frontend/      # React + TypeScript (see frontend/README.md)
```
=======
# Interneers Lab - Backend in Python

Welcome to the **Interneers Lab 2026** Python backend! This serves as a minimal starter kit for learning and experimenting with:
- **Django** (Python)
- **MongoDB** (via Docker Compose)
- Development environment in **VSCode** (recommended)

**What this repository does:** It provides a Django app with a simple **Hello API** (`GET` and `POST` `/hello/`) that accepts a `name` parameter (query for GET, JSON body for POST) and returns a greeting. The code is structured using **hexagonal architecture** (domain + adapters). See [ARCHITECTURE.md](ARCHITECTURE.md) for the layering.

**Important:** Use the **same email** you shared during onboarding when configuring Git and related tools. That ensures consistency across all internal systems.

>>>>>>> 85634b6 (Week 1: Hello API  with a hexagonal layout and tested the API using postman)

---

## Table of Contents

<<<<<<< HEAD
1. [Getting Started with Git & Forking](#getting-started-with-git-and-forking)
2. [Prerequisites & where to find them](#prerequisites--where-to-find-them)
3. [Setting up & running](#setting-up--running)
4. [Development Workflow](#development-workflow)
   - [Pushing Your First Change](#pushing-your-first-change)
5. [Making your first change](#making-your-first-change)
6. [Running Tests](#running-tests)
7. [Frontend Setup](#frontend-setup)
8. [Further Reading](#further-reading)

---

## Getting Started with Git and Forking

### 1. Setting up Git and the Repo

1. **Install Git** (if not already):
   - **macOS**: [Homebrew](https://brew.sh/) users can run `brew install git`.
   - **Windows**: Use [Git for Windows](https://gitforwindows.org/).
   - **Linux**: Install via your distro's package manager, e.g., `sudo apt-get install git` (Ubuntu/Debian).

2. **Configure Git** with your name and email:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com" # Use the same email you shared during onboarding
   ```

3. **What is Forking?**

   Forking a repository on GitHub creates your own copy under your GitHub account, where you can make changes independently without affecting the original repo. Later, you can make pull requests to merge changes back if needed.

4. Fork the Rippling/interneers-lab repository (ensure you're in the correct org or your personal GitHub account, as directed).
5. **Clone** your forked repo:
   ```bash
   git clone git@github.com:<YourUsername>/interneers-lab.git
   cd interneers-lab
   ```

## Prerequisites & where to find them

Prerequisites (Python, Go, Node, Docker, etc.) and how to verify your setup are documented in each part of the repo:

- **[backend/python/README.md](backend/python/README.md)** — Python/Django, virtualenv, MongoDB
- **[backend/go/README.md](backend/go/README.md)** — Go, MongoDB
- **[frontend/README.md](frontend/README.md)** — Node, Yarn, React

Use the README for the part you're working on.

---

## Setting up & running

Setup and run instructions live in the domain READMEs:

- **Python backend:** [backend/python/README.md](backend/python/README.md) — venv, dependencies, `runserver`, Docker Compose for MongoDB
- **Go backend:** [backend/go/README.md](backend/go/README.md) — `make setup`, `make build-and-run`, Docker Compose
- **Frontend:** [frontend/README.md](frontend/README.md)
=======
1. [Developer guide (Week 1)](#developer-guide-week-1)
2. [Prerequisites & Tooling](#prerequisites--tooling)
3. [Setting Up the Project](#setting-up-the-project)
4. [Running Services](#running-services)
   - [Backend: Django](#backend-django)
   - [Database: MongoDB via Docker Compose](#database-mongodb-via-docker-compose)
5. [Verification of Installation](#verification-of-installation)
6. [Development Workflow](#development-workflow)
   - [Recommended VSCode Extensions](#recommended-vscode-extensions)
   - [Making Changes & Verifying](#making-changes--verifying)
   - [Pushing Your First Change](#pushing-your-first-change)
7. [Making Your First Change](#making-your-first-change)
   - [Starter 0](#starter-0-changes)
   - [Starter 1](#starter-1-changes)
8. [Running Tests (Optional)](#running-tests-optional)
9. [Hot Reloading](#hot-reloading)
10. [MongoDB Connection](#mongodb-connection)
11. [Further Reading](#further-reading)
12. [Important Note on settings.py](#important-note-on-settingspy)

---

## Developer guide (Week 1)

After setup (see below), run the server with `python manage.py runserver 8001`. The Hello API is available at:

- **GET** `http://127.0.0.1:8001/hello/?name=YourName` — `name` is a query parameter.
- **POST** `http://127.0.0.1:8001/hello/` with JSON body `{"name": "YourName"}` — `name` is the payload.

The server prints the received `name` to the console and responds with `{"message": "Hello, YourName!"}`. If `name` is missing or empty, the response uses `"World"`.

**Project layout (hexagonal):** Business logic lives in `django_app/domain/` (e.g. `domain/hello.py`). HTTP handling lives in `django_app/adapters/` (e.g. `adapters/hello_views.py`). Routes are in `django_app/urls.py`. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

**Testing with Postman:** Create a GET request to `http://127.0.0.1:8001/hello/?name=Bob` or a POST request to `http://127.0.0.1:8001/hello/` with body `{"name": "Bob"}` (Content-Type: application/json). You should get `{"message": "Hello, Bob!"}`.

---

## Prerequisites & Tooling

These are the essential tools you need:

1. **Homebrew (macOS Only)**

   **Why?**

   Homebrew is a popular package manager for macOS, making it easy to install and update software (like Python, Docker, etc.).

   **Install**:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Python 3.14** (3.12 or higher required)

   **Why 3.14?**

   This is the recommended version for the module's Python-related tasks, ensuring consistency across projects.

   **Install or Upgrade**:

   - macOS (with Homebrew): `brew install python` or use [pyenv](https://github.com/pyenv/pyenv):
     ```bash
     brew install pyenv
     brew update && brew upgrade pyenv
     pyenv install 3.14.3
     ```
   - Windows: [Download from python.org](https://www.python.org/downloads/) (ensure it's 3.14)
   - Linux: Use your distro's package manager or pyenv

   **Verify**:

   ```bash
   python3 --version
   ```
   You should see something like `Python 3.14.x`.

   If you are getting an older version, you can either:
   - Use the full path: `~/.pyenv/versions/3.14.3/bin/python`
   - Or update your `.bashrc` / `.zshrc`:
     ```bash
     vim ~/.zshrc   # or any preferred editor of your choice
     alias python3="/path/to/python3.14"
     source ~/.zshrc # or ~/.bashrc
     ```

3. **virtualenv** or built-in `venv`

   **Why?**

   A virtual environment keeps project dependencies isolated from your system Python.

   **Install**
   - `pip3 install virtualenv` (if needed)
   - or use `python3 -m venv venv`

   **Verify**

   - Try to activate the venv using the following command:
     ```bash
     source venv/bin/activate         # macOS/Linux
     .\venv\Scripts\activate          # Windows
     ```

   - In most machines, your terminal prompt will be prefixed with something like `(venv)`.

   Check which Python is being used:

   - macOS/Linux:
     ```bash
     which python
     ```
     This should return a path inside the `venv/` directory (e.g., `.../backend/python/venv/bin/python`)

   - Windows:
     ```
     where python
     ```
     This should return a path inside `venv\Scripts\python.exe`.


4. **Docker** & **Docker Compose**

   **Why?**

   We use Docker to run MongoDB (and potentially other services) in containers, preventing "works on my machine" issues.

   **Install**

   - [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
   - [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

   **Verify**

   Verify version and successful installation with `docker --version` and `docker compose version`.


5. **API & MongoDB Tools**
   - **[Postman](https://www.postman.com/downloads/)**, **[Insomnia](https://insomnia.rest/download)**, or **[Paw](https://paw.cloud/client) (only for mac)** for API testing
   - **[MongoDB Compass](https://www.mongodb.com/try/download/compass)** or a **[VSCode MongoDB](https://code.visualstudio.com/docs/azure/mongodb)** extension

---

## Setting Up the Project

### Create a Python Virtual Environment

The python virtual env should be created inside the `backend/python` directory. Run the following commands:

```bash
cd backend/python
python3 -m venv venv
```

To activate the virtual environment:

```bash
# macOS/Linux
source venv/bin/activate
```
```Powershell
# on Windows Powershell:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\activate
```

### Install Python Dependencies

```bash
pip install --upgrade pip
pip3 install -r requirements.txt
```

By default, **requirements.txt** includes:
- **Django** 6.0.2
- **pymongo** 4.16.0 (MongoDB driver)

**Check your `.gitignore`**
Make sure `venv/` and other temporary files aren't committed.

---

## Running Services

### Backend: Django

Navigate to the `backend/python` directory:

```bash
cd backend/python
```

Start the Django server on port `8001`:

```bash
python manage.py runserver 8001
```

Open [http://127.0.0.1:8001/hello/](http://127.0.0.1:8001/hello/) to see the **"Hello World"** endpoint.

---

### Database: MongoDB via Docker Compose

Inside `backend/python`, you'll find a `docker-compose.yaml`.

To start MongoDB via Docker Compose:

```bash
docker compose up -d
```

Verify with:

```bash
docker compose ps
```

MongoDB is now running on `localhost:27019`. Connect using `root` / `example` or update credentials as needed.

---

## Verification of Installation

- **Python**: `python3 --version` (should be 3.12+)
- **Django**: `python -c "import django; print(django.get_version())"` (should be 6.0.2)
- **Docker**: `docker --version`
- **Docker Compose**: `docker compose version`

Confirm that all meet the minimum version requirements.
>>>>>>> 85634b6 (Week 1: Hello API  with a hexagonal layout and tested the API using postman)

---

## Development Workflow

<<<<<<< HEAD
### Making your first change

Step-by-step tutorials live in the domain READMEs:

- **[backend/python/README.md](backend/python/README.md)** — Django starters (e.g. Hello World, Hello {name} API)
- **[backend/go/README.md](backend/go/README.md)** — Go hello-world and APIs
- **[frontend/README.md](frontend/README.md)** — React hello-world and APIs
=======
### Recommended VSCode Extensions

- **Python (Microsoft)**
  Provides language server support, debugging, linting, and IntelliSense for Python code.

- **Django** (optional but helpful)
  Offers syntax highlighting and code snippets tailored for Django projects.

- **Docker**
  Allows you to visualize, manage, and interact with Docker containers and images directly in VSCode.

- *(Optional)* **MongoDB for VSCode**
  Lets you connect to and browse your MongoDB databases, run queries, and view results without leaving VSCode.

---

### Making Your First Change

## Backend:

### Starter 0 changes:

1. Edit the `hello_world` function in `django_app/urls.py`.
2. Refresh your browser at [http://127.0.0.1:8001/hello/](http://127.0.0.1:8001/hello/).

### Starter 1 changes:

##### Creating and Testing a Simple "Hello, {name}" API (via Query Parameters)

This section explains how to create a Django endpoint that reads a `name` parameter from the **query string** (e.g., `/?name=Bob`).

---

#### 1. Define the View Function

Open `django_app/urls.py`. Below, we'll define a function that looks for a `name` query parameter in `request.GET`:

```python
# django_app/urls.py

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def hello_name(request):
    """
    A simple view that returns 'Hello, {name}' in JSON format.
    Uses a query parameter named 'name'.
    """
    # Get 'name' from the query string, default to 'World' if missing
    name = request.GET.get("name", "World")
    return JsonResponse({"message": f"Hello, {name}!"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', hello_name),
    # Example usage: /hello/?name=Bob
    # returns {"message": "Hello, Bob!"}
]
```

---

#### 2. Run the Django Server

Activate your virtual environment (if not already active):

```bash
source venv/bin/activate         # macOS/Linux
.\venv\Scripts\activate          # Windows
```

Install dependencies (if you haven't):
```bash
cd backend/python  # if you are not inside backend/python already.
pip3 install -r requirements.txt
```

Start the server on port 8001:
```bash
python manage.py runserver 8001
```

You should see:
```
Starting development server at http://127.0.0.1:8001/
```

#### Test the Endpoint with Postman (or Insomnia/Paw)

Install a REST client like Postman (if you haven't already).

Create a new GET request.

Enter the endpoint, for example:
```
http://127.0.0.1:8001/hello/?name=Bob
```

Send the request. You should see a JSON response:
```json
{
  "message": "Hello, Bob!"
}
```

#### Congratulations! You wrote your first own API.

---
>>>>>>> 85634b6 (Week 1: Hello API  with a hexagonal layout and tested the API using postman)

### Pushing Your First Change

1. **Stage and commit**:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```
2. **Push to your forked repo (main branch by default):**
   ```bash
   git push origin main
   ```

---

<<<<<<< HEAD
## Running Tests

See the domain READMEs for how to run tests in each stack:

- [backend/python/README.md](backend/python/README.md)
- [backend/go/README.md](backend/go/README.md)
- [frontend/README.md](frontend/README.md)
=======
## Running Tests (Optional)

### Django Tests

```bash
cd backend/python
python manage.py test
```

### Docker

```bash
docker compose ps
```
Note: This command displays the status of the containers, including whether they are running, their assigned ports, and their names, as defined in the docker-compose.yaml file. If you have set up a MongoDB server using Docker and connected it to your Django application, you can use this command to verify that the MongoDB container is running properly.

---

## Hot Reloading

Django's development server supports hot reloading out of the box. When you modify any Python file, the server automatically detects the change and restarts. Simply save your file and refresh the browser to see your changes.

---

## MongoDB Connection

MongoDB connections differ depending on your setup:

### Local Development

When running the project locally, MongoDB is exposed on port **27019**:

```
mongodb://root:example@localhost:27019/?authSource=admin
```

### Using Environment Variables

To ensure flexibility across environments, use environment variables for the MongoDB connection. For example:

#### Example `settings.py` (Django + pymongo):
```python
# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()
MONGO_USER = os.getenv("MONGO_USER", "root")
MONGO_PASS = os.getenv("MONGO_PASS", "example")
MONGO_PORT = os.getenv("MONGO_PORT", "27019")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")

client = MongoClient(
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
)

DATABASES = {}
```
>>>>>>> 85634b6 (Week 1: Hello API  with a hexagonal layout and tested the API using postman)

---

## Further Reading

<<<<<<< HEAD
Each domain has detailed README with links to relevant docs. In general:

- **Django:** [docs.djangoproject.com](https://docs.djangoproject.com/)
- **React:** [react.dev](https://react.dev/learn)
- **Go:** [go.dev/doc](https://go.dev/doc/)
- **MongoDB:** [docs.mongodb.com](https://docs.mongodb.com/)
- **Docker Compose:** [docs.docker.com/compose](https://docs.docker.com/compose/)
=======
- Django: https://docs.djangoproject.com/en/6.0/
- MongoDB: https://docs.mongodb.com/
- Docker Compose: https://docs.docker.com/compose/
- pymongo: https://pymongo.readthedocs.io/en/stable/

---

## Important Note on `settings.py`
- You should commit `settings.py` so the Django configuration is shared.
- However, never commit secrets (API keys, passwords) directly. Use environment variables or `.env` files (excluded via `.gitignore`).

---

## Common Commands Reference

```bash
# Virtual environment
python3 -m venv venv                        # Create virtual environment
source venv/bin/activate                     # Activate (macOS/Linux)
.\venv\Scripts\activate                      # Activate (Windows)
deactivate                                   # Deactivate

# Dependencies
pip install -r requirements.txt              # Install dependencies
pip freeze > requirements.txt                # Update requirements file

# Django
python manage.py runserver 8001              # Start dev server on port 8001
python manage.py test                        # Run tests

# Docker / MongoDB
docker compose up -d                         # Start MongoDB
docker compose down                          # Stop MongoDB
docker compose ps                            # List running containers
docker compose logs -f                       # View logs
```
>>>>>>> 85634b6 (Week 1: Hello API  with a hexagonal layout and tested the API using postman)
