def get_greeting(name):
    if not name or not name.strip():
        name = "World"
    return f"Hello, {name.strip()}!"
