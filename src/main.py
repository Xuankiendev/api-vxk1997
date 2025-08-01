from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.api import example
from src.db import createTables

createTables()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup")
def signupPage(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login")
def loginPage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

app.include_router(example.router, prefix="/api")
