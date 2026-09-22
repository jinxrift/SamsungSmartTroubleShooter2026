from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Samsung Smart Troubleshooter")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)