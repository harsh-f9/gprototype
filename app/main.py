from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routes import forms, auth, api
from app.database import init_db

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(title="GreenBridge FastAPI Prototype", lifespan=lifespan)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)  # Auth routes first
app.include_router(forms.router)
app.include_router(api.router)  # API routes for streaming

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/debug_routes")
async def debug_routes():
    return [{"path": route.path, "name": route.name} for route in app.routes]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)

