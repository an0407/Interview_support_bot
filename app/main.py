from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import smtplib

from app.database import Base, engine
from app.routers import chat_router, db_populate_router

# 1. Template renderer
templates = Jinja2Templates(directory="app/templates") 

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as create:
        await create.run_sync(Base.metadata.create_all)  
    yield

app = FastAPI(lifespan=lifespan)

# 2. Include API router
app.include_router(chat_router.router)
app.include_router(db_populate_router.router)

# 3. Serve the chatbot UI
@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_ui(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})