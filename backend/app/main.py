from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import endpoints, stats
from app.scheduler import start_scheduler, load_jobs_from_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    await load_jobs_from_db()
    yield
    # Shutdown
    # scheduler.shutdown() # Optional, but good practice

app = FastAPI(title="API Monitor", lifespan=lifespan)

# CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
    "*" # For development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/endpoints", tags=["Endpoints"])
app.include_router(stats.router, tags=["Stats"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
