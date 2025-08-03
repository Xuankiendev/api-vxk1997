from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
import importlib
import json
import os
import traceback
import logging

from src import auth
from src.db import getDb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Platform", version="1.0.0")

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

templates = Jinja2Templates(directory="templates")
app.include_router(auth.router)

try:
    with open("assets/apis.json", "r") as f:
        apis = json.load(f)
except FileNotFoundError:
    logger.warning("apis.json not found, creating empty config")
    apis = {}
except Exception as e:
    logger.error(f"Error loading apis.json: {e}")
    apis = {}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.get("/")
async def home(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return HTMLResponse("<h1>Welcome to API Platform</h1><p>Home page template not found</p>")

@app.get("/signup")
async def signupPage(request: Request):
    try:
        return templates.TemplateResponse("signup.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading signup page: {e}")
        return HTMLResponse("<h1>Error</h1><p>Signup page template not found</p>", status_code=500)

@app.get("/login")
async def loginPage(request: Request):
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading login page: {e}")
        return HTMLResponse("<h1>Error</h1><p>Login page template not found</p>", status_code=500)

@app.get("/dashboard")
async def dashboardPage(request: Request):
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading dashboard page: {e}")
        return HTMLResponse("<h1>Dashboard</h1><p>Dashboard template not found</p>")

@app.get("/privacy")
async def privacyPage(request: Request):
    try:
        return templates.TemplateResponse("privacy.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading privacy page: {e}")
        return HTMLResponse("<h1>Privacy Policy</h1><p>Privacy template not found</p>")

@app.get("/test")
async def test_endpoint():
    return {"message": "API Platform is working!", "status": "success"}

@app.get("/test-db")
async def test_database():
    try:
        from src.db import getDb, User
        db_gen = getDb()
        db = next(db_gen)
        result = db.execute("SELECT 1").scalar()
        db.close()
        return {"status": "Database connection successful", "result": result}
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Database connection failed", "detail": str(e)}
        )

@app.get("/api/{apiName}")
async def dynamicApi(apiName: str, request: Request, db: Session = Depends(getDb)):
    if apiName not in apis:
        raise HTTPException(status_code=404, detail="API not found")

    try:
        module = importlib.import_module(f"src.api.{apiName}")
    except ImportError as e:
        logger.error(f"Failed to import module src.api.{apiName}: {e}")
        raise HTTPException(status_code=500, detail="API module import failed")
    except Exception as e:
        logger.error(f"Unexpected error importing module: {e}")
        raise HTTPException(status_code=500, detail="API module import failed")

    params = {}
    for param in apis[apiName]["params"]:
        value = request.query_params.get(param)
        if value is None:
            raise HTTPException(status_code=422, detail=f"Missing parameter: {param}")
        params[param] = value

    try:
        result = await module.run(params, db)
        return JSONResponse(content={"success": True, "ownerAPI": "VuXuanKien1997", "data": result})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in API {apiName}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e) or "Unknown error occurred")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
