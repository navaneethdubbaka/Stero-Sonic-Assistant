from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
try:
    from backend.api import voice, commands, chatbot, system
except ImportError:
    # When running from backend directory
    from api import voice, commands, chatbot, system

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

@app.get("/")
async def root():
    return {"message": "Stereo Sonic Assistant API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

