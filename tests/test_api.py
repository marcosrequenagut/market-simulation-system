from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    """Health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulate_basci():
    """Basic simulation returns expected keys"""
    responde = client.post("/simulate", json={
        "initial_investment": 10000,
        "annual_rate": 0.10,
        "years": 10
    })
    assert responde.status_code == 200
    data = responde.json()
    assert "cagr" in data
    assert "compound_interest" in data
    assert "monte_carlo" in data


def test_simulate_invalid_investment():
    """Negative investment returns 400"""
    response = client.post("/simulate", json={
        "initial_investment": -1000,
        "annual_rate": 0.10,
        "years": 10
    })
    assert response.status_code == 400


def test_simulate_gaussian_model():
    """Gaussian model returns valid results"""
    response = client.post("/simulate", json={
        "initial_investment": 5000,
        "annual_rate": 0.07,
        "years": 5,
        "model": "gaussian"
    })
    assert response.status_code == 200
    assert response.json()["monte_carlo"]["simulations"] == 1000


def test_metrics_basic():
    """Basic metrics calculation returns expected keys"""
    response = client.post("/metrics", json={
        "initial_value": 1000,
        "final_value": 2500,
        "years": 10,
        "annual_volatility": 0.15
    })
    assert response.status_code == 200
    data = response.json()
    assert "cagr" in data
    assert "total_return" in data
    assert "shape_ratio" in data
    assert "annual_volatility" in data


def test_metrics_invalid_input():
    """Invalid input (zero initial value) returns 400"""
    response = client.post("/metrics", json={
        "initial_value": 0,
        "final_value": 2500,
        "years": 10,
        "annual_volatility": 0.15
    })
    assert response.status_code == 400


def test_compare_strategies_basic():
    """Basic comparison of multiple strategies returns expected structure"""
    response = client.post("/compare", json={
        "years": 10,
        "strategies": [
            {
                "name": "Conservative",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.05
            },
            {
                "name": "Aggressive",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.10
            }
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert "years" in data
    assert "winner" in data
    assert "strategies" in data
    assert len(data["strategies"]) == 2
    assert data["strategies"][0]["final_value"] >= data["strategies"][1]["final_value"]


def test_compare_strategies_invalid_count():
    """Less than 2 strategies returns 400"""
    response = client.post("/compare", json={
        "years": 5,
        "strategies": [
            {
                "name": "Conservative",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.05
            }
        ]
    })
    assert response.status_code == 400


def test_compare_strategies_invalid_years():
    """A year equal or fewer than 0 returns 400"""
    response = client.post("/compare", json={
        "years": 0,
        "strategies": [
            {
                "name": "Conservative",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.05
            },
            {
                "name": "Aggressive",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.10
            }
        ]
    })
    assert response.status_code == 400


def test_compare_strategies_exception(monkeypatch):
    def boom(*args, **kwargs):
        raise ValueError("forced error")

    monkeypatch.setattr(
        "app.routers.compare.calculate_compound_interest",
        boom
    )

    response = client.post("/compare", json={
        "years": 10,
        "strategies": [
            {
                "name": "A",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.05
            },
            {
                "name": "B",
                "initial_investment": 10000,
                "monthly_contribution": 500,
                "annual_rate": 0.10
            }
        ]
    })

    assert response.status_code == 400
