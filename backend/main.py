from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Web research / crawl logs (core.tools, services.*) use INFO; set LOG_LEVEL=DEBUG for more detail.
_log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
if not logging.root.handlers:
    logging.basicConfig(
        level=_log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
else:
    logging.getLogger().setLevel(_log_level)
    for _log_name in (
        "core.tools",
        "services.cloudflare_crawl_service",
        "services.web_search_results_service",
    ):
        logging.getLogger(_log_name).setLevel(_log_level)

# Import routers
try:
    from backend.api import voice, commands, chatbot, system, reminders, robot
except ImportError:
    # When running from backend directory
    from api import voice, commands, chatbot, system, reminders, robot

app = FastAPI(title="Stereo Sonic Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(commands.router, prefix="/api/commands", tags=["Commands"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(robot.router, prefix="/api/robot", tags=["Robot"])

@app.get("/")
async def root():
    return {"message": "Stereo Sonic Assistant API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

