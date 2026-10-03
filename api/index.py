from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application
from config import BOT_TOKEN
from database import init_db

init_db()

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Top-level ASGI variable required by Vercel Python Runtime
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await telegram_app.initialize()

@app.post("/")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(status_code=200)