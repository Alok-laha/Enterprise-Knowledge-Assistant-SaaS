from fastapi import Depends, FastAPI
from sqlalchemy import text

from app.api.v1.tenants import router as tenants_router
from app.db.database import get_db

app = FastAPI(
    title="Enterprise Knowledge Assistant",
    version="1.0.0"
)

app.include_router(tenants_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "The Enterprise Knowledge Assistant API is running smoothly."
    }


@app.get("/health/db")
def test_db(db=Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"database_connected": result == 1}