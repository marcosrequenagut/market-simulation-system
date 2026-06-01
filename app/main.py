from fastapi import FastAPI
from app.routers.simulation import router as simulation_router

app = FastAPI(title="SP500 Analyzer", version="0.1.0")

app.include_router(simulation_router)


@app.get("/health")
def health():
    return {"status": "ok"}
