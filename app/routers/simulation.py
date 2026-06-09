from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.engine.calculator import calculate_cagr, calculate_compound_interest
from app.engine.montecarlo import run_monte_carlo, run_monte_carlo_lognormal

router = APIRouter(prefix="/simulate", tags=["simulation"])


class SimulationRequest(BaseModel):
    initial_investment: float
    monthly_contribution: float = 0.0
    annual_rate: float
    annual_volatility: float = 0.15
    years: int
    simulations: int = 1000
    model: str = "lognormal"


@router.post("/", responses={400: {"description": "Invalid request"}})
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
            monte_carlo_result = run_monte_carlo_lognormal(
                request.initial_investment,
                request.annual_rate,
                request.annual_volatility,
                request.years,
                request.simulations,
                request.monthly_contribution
            )
        else:
            monte_carlo_result = run_monte_carlo(
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
