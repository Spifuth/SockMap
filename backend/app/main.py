from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import docker

app = FastAPI(
    title="SockMap API",
    description="Auto-wiki your Docker stack - Read Docker socket and generate visual documentation",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(docker.router)


@app.get("/")
async def root():
    return {
        "name": "SockMap API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
