import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your router
from backend.api.routes import router as detection_router

# Initialize FastAPI app
app = FastAPI(
    title="Smart HSRP Monitoring API",
    description="Helmet detection, HSRP classification, and OCR pipeline",
    version="1.0.0"
)

# Allow CORS for frontend / UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your router
app.include_router(detection_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "OK", "message": "Smart HSRP API is running"}

# Optional root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Smart HSRP Monitoring API"}

# Entry point
if __name__ == "__main__":
    # 2025-style high-performance uvicorn run
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Remove in production
        workers=1,    # Increase for multi-core CPUs
        log_level="info"
    )
