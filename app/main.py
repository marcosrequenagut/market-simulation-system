from fastapi import FastAPI
from app.routers.simulation import router as simulation_router
from app.routers.metrics import router as metrics_router

app = FastAPI(title="SP500 Analyzer", version="0.1.0")

app.include_router(simulation_router)
app.include_router(metrics_router)


@app.get("/health")
def health():
    return {"status": "ok"}
