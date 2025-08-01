from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api import example, github_info
from . import auth, chat

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(example.router)
app.include_router(github_info.router)

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
