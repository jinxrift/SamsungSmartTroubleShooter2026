from fastapi import FastAPI

app = FastAPI(title="Samsung Smart Troubleshooter")


@app.get("/health")
def health():
    return {"status": "ok"}