from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, photos, receipts, chat, vault, stats, people, auth_google
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PersonaLens API")

# CORS setup
# CORS setup - Explicitly allowing frontend origins
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"DEBUG: Incoming request: {request.method} {request.url}")
    print(f"DEBUG: Origin header: {request.headers.get('origin')}")
    response = await call_next(request)
    return response

from fastapi import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler

@app.exception_handler(FastAPIHTTPException)
async def custom_http_exception_handler(request, exc):
    """Pass through HTTP exceptions but ensure CORS headers are present."""
    origin = request.headers.get("origin", "")
    response = await http_exception_handler(request, exc)
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch unexpected errors only (not HTTPException)."""
    if isinstance(exc, FastAPIHTTPException):
        return await custom_http_exception_handler(request, exc)
    print(f"CRITICAL ERROR: {exc}")
    import traceback
    traceback.print_exc()
    origin = request.headers.get("origin", "")
    response = JSONResponse(
        status_code=500,
        content={"message": str(exc) or "Internal Server Error"},
    )
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(receipts.router)
app.include_router(chat.router)
app.include_router(vault.router)
app.include_router(people.router)
app.include_router(stats.router)
app.include_router(auth_google.router)

# Mount uploads directory to serve images
# WARNING: In production, use Nginx/S3/CDN and ensure sensitive files are NOT public
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="static_uploads")

@app.get("/")
def read_root():
    return {"message": "Welcome to PersonaLens API"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
