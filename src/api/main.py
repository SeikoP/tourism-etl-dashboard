from fastapi import FastAPI
from . import routes

app = FastAPI(title="CulturaTour - Data Collector & Booking API")

app.include_router(routes.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
