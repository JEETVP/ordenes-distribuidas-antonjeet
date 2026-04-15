from fastapi import FastAPI

from db import engine
from models import Base

app = FastAPI(title="Auth Service")


@app.on_event("startup")
def startup():
    if engine is not None:
        Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"service": "auth-service"}
