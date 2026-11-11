from fastapi import FastAPI
app = FastAPI(title="Analytics")
@app.get("/health")
async def health():
    return {"status": "ok"}
