from fastapi import FastAPI
app = FastAPI(title="Notifier")
@app.get("/health")
async def health():
    return {"status": "ok"}
