from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.engine.calculator import calculate_compound_interest


router = APIRouter(prefix="/compare", tags=["compare"])


class Strategy(BaseModel):
    name: str
    initial_investment: float
    monthly_contribution: float = 0.0
    annual_rate: float


class CompareRequest(BaseModel):
    years: int
    strategies: list[Strategy]


@router.post("/")
def compare_strategies(request: CompareRequest):
    """
    Compare multiple investments strategies side by side.
    Returns results for each strategy sorted by final value.
    """
    if len(request.strategies) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 strategies are required for comparison"
        )

    if request.years <= 0:
        raise HTTPException(
            status_code=400,
            detail="Years must be greater than 0"
        )

    try:
        results = []
        for strategy in request.strategies:

            result = calculate_compound_interest(
                initial_investment=strategy.initial_investment,
                monthly_contribution=strategy.monthly_contribution,
                annual_rate=strategy.annual_rate,
                years=request.years
            )
            results.append({
                "name": strategy.name,
                "initial_investment": strategy.initial_investment,
                "monthly_contribution": strategy.monthly_contribution,
                "annual_rate": strategy.annual_rate,
                "years": request.years,
                "final_value": result["final_value"],
                "total_invested": result["total_invested"],
                "total_interes": result["total_interest"]
            })

        # Sort by final value (descending)
        results.sort(key=lambda x: x["final_value"], reverse=True)

        return {
            "years": request.years,
            "winner": results[0]["name"],
            "strategies": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
