import pytest
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
