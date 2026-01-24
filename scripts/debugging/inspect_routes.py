
from src.server import app
from starlette.routing import Route, Mount

print("Registered Routes:")
for route in app.routes:
    if isinstance(route, Route):
        print(f" - Path: {route.path} | Methods: {route.methods}")
    elif isinstance(route, Mount):
        print(f" - Mount: {route.path} | Name: {route.name}")
