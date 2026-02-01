import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Set required env vars to avoid startup errors
os.environ["GCP_PROJECT_ID"] = "profitscout-fida8"

try:
    from server import app

    print("\n=== App Inspection ===")
    print(f"App Type: {type(app)}")

    print("\n--- app.user_middleware ---")
    if hasattr(app, "user_middleware"):
        for m in app.user_middleware:
            # print(f"- {m.cls.__name__} (Args: {m.options})") # options/kwargs varies
            print(f"- {m.cls.__name__}")
    else:
        print("No user_middleware attribute")

    print("\n--- app.middleware ---")
    # app.middleware is a decorator method in Starlette, not a list. Skipping.
    print("Skipping app.middleware inspection (it is a method)")

    print("\n--- app.routes ---")
    if hasattr(app, "routes"):
        for route in app.routes:
            print(f"- {route.path} ({type(route).__name__}) name={getattr(route, 'name', 'N/A')}")
            if type(route).__name__ == "Mount":
                sub_app = getattr(route, "app", None)
                print(f"  -> Mounted App: {type(sub_app)}")
                if hasattr(sub_app, "user_middleware"):
                    print(f"  -> Sub-app Middleware: {len(sub_app.user_middleware)}")
                    for m in sub_app.user_middleware:
                        print(f"     * {m.cls.__name__} {m.options}")
    else:
        print("No routes attribute")

except Exception as e:
    print(f"Error inspecting app: {e}")
