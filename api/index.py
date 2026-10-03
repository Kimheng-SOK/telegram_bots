from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import os

from config import BOT_TOKEN
from database import init_db

# Initialize database
init_db()

# Build the python-telegram-bot Application
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Register your handlers here (or import from your handlers module)
# telegram_app.add_handler(CommandHandler("start", start_command))

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initializes python-telegram-bot application state
    await telegram_app.initialize()

@app.post("/api/index")
async def process_webhook(request: Request):
    """Receives webhook updates from Telegram."""
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)

    # Process update asynchronously
    await telegram_app.process_update(update)
    return Response(status_code=200)

@app.get("/")
def health_check():
    return {"status": "bot is running via vercel webhook"}