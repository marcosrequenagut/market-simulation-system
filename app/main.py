from fastapi import FastAPI
from app.routers.simulation import router as simulation_router
from app.routers.metrics import router as metrics_router
from app.routers.compare import router as compare_router
from app.routers.market import router as market_router

app = FastAPI(title="Market Analyzer", version="0.1.0")

app.include_router(simulation_router)
app.include_router(metrics_router)
app.include_router(compare_router)
app.include_router(market_router)


@app.get("/health")
def health():
    return {"status": "ok"}
