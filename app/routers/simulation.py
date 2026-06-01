from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.engine.calculator import calculate_cagr, calculate_compound_interest
from app.engine.montecarlo import run_monter_carlo, run_monter_carlo_lognormal
from app.engine.data import get_sp500_data

router = APIRouter(prefix="/simulate", tags=["simulation"])


class SimulationRequest(BaseModel):
    initial_investment: float
    monthly_contribution: float = 0.0
    annual_rate: float
    years: int
    simulations: int = 1000
    model: str = "lognormal"


@router.post("/")
def simulate(request: SimulationRequest):
    """
    Run a full portfolio simulation.
    Returns CAGR, compound interest and Monte Carlo results.
    """

    try:

        compound_result = calculate_compound_interest(
            request.initial_investment,
            request.monthly_contribution,
            request.annual_rate,
            request.years
        )

        cagr_result = calculate_cagr(
            request.initial_investment,
            request.initial_investment * (1 + request.annual_rate) ** request.years,
            request.years
        )

        if request.model == "lognormal":
            monte_carlo_result = run_monter_carlo_lognormal(
                request.initial_investment,
                request.annual_rate,
                0.15,
                request.years,
                request.simulations
            )
        else:
            monte_carlo_result = run_monter_carlo(
                request.initial_investment,
                request.annual_rate,
                0.15,
                request.years,
                request.simulations
            )

        return {
            "compound_interest": compound_result,
            "cagr": round(cagr_result, 4),
            "monte_carlo": monte_carlo_result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sp500/{period}")
def get_sp500(period: str = "10y"):
    """
    Get real S&P 500 historical data and calculate statistics.
    """
    try:
        return get_sp500_data(period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
