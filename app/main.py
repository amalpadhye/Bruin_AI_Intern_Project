"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import scan, menus, uploads, admin, scraper_bulk, store_scraped
from app.config import settings

app = FastAPI(
    title="ForkU API",
    description="Food tracking and social app for UCLA students",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scan.router)
app.include_router(menus.router)
app.include_router(uploads.router)
app.include_router(admin.router)
app.include_router(scraper_bulk.router)
app.include_router(store_scraped.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ForkU API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

