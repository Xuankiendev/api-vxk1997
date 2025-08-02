import importlib
import json
from fastapi import FastAPI

def loadRouters(app: FastAPI):
    with open("assets/apis.json") as f:
        apis = json.load(f)

    for apiName in apis:
        try:
            module = importlib.import_module(f"src.api.{apiName}")
            router = getattr(module, "router", None)
            if router:
                app.include_router(router)
        except Exception as e:
            print(f"Failed to load router for '{apiName}': {e}")
