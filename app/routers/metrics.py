from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.engine.calculator import calculate_cagr


router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsRequest(BaseModel):
    initial_value: float
    final_value: float
    years: int
    annual_volatility: float = 0.15


@router.post("/")
def get_metrics(request: MetricsRequest):
    """
    Calculate key investment metrics.
    Returns CAGR, total return, Sharpe ratio and annualized volatility.
    """
    try:
        cagr = calculate_cagr(
            request.initial_value,
            request.final_value,
            request.years
        )

        total_return = (request.final_value - request.initial_value) / request. initial_value

        risk_free_rate = 0.04
        sharpe_ratio = (cagr - risk_free_rate) / request.annual_volatility

        return {
            "cagr": round(cagr, 4),
            "total_return": round(total_return, 4),
            "shape_ratio": round(sharpe_ratio, 4),
            "annual_volatility": request.annual_volatility
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
