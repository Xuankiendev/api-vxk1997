from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import importlib
import json
import os
import traceback

from . import auth
from .db import getDb

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(auth.router)

with open(os.path.join(os.path.dirname(__file__), "../assets/apis.json")) as f:
    apis = json.load(f)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup")
async def signupPage(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login")
async def loginPage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard")
async def dashboardPage(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/privacy")
async def privacyPage(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/api/{apiName}")
async def dynamicApi(apiName: str, request: Request, db: Session = Depends(getDb)):
    if apiName not in apis:
        raise HTTPException(status_code=404, detail="API not found")

    try:
        module = importlib.import_module(f"src.api.{apiName}")
    except Exception:
        raise HTTPException(status_code=500, detail="API module import failed")

    params = {}
    for param in apis[apiName]["params"]:
        value = request.query_params.get(param)
        if value is None:
            raise HTTPException(status_code=422, detail=f"Missing parameter: {param}")
        params[param] = value

    try:
        result = await module.run(params, db)
        return JSONResponse(content={"success": True, "owner": "VuXuanKien1997", "data": result})
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e) or "Unknown error occurred")
