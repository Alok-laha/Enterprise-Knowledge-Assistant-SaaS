from fastapi import FastAPI, Depends
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://myuser:mypassword@localhost:5432/mydb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    title="Enterprise Knowledge Assistant",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "The Enterprise Knowledge Assistant API is running smoothly."
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health/db")
def test_db(db=Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"database_connected": result == 1}