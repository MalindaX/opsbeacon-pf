import pytest
from app.app import create_app
from app.models import db, Incident

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_check(client):
    """Test the /health liveness and readiness probe"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_metrics_endpoint(client):
    """Test that Prometheus scrapes /metrics successfully"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"flask_http_request_duration_seconds" in response.data or b"opsbeacon" in response.data

def test_create_and_get_incident(client):
    """Test incident creation and retrieval via API"""
    new_incident = {
        "title": "Payment gateway latency high",
        "service_name": "payment-api",
        "severity": "HIGH"
    }
    create_res = client.post("/api/incidents", json=new_incident)
    assert create_res.status_code == 201
    created_data = create_res.get_json()
    assert created_data["title"] == "Payment gateway latency high"
    assert created_data["severity"] == "HIGH"
    assert created_data["status"] == "OPEN"

    # Verify retrieval
    get_res = client.get("/api/incidents")
    assert get_res.status_code == 200
    items = get_res.get_json()
    assert len(items) == 1
    assert items[0]["id"] == created_data["id"]

def test_resolve_incident(client):
    """Test resolving an active incident"""
    create_res = client.post("/api/incidents", json={"title": "Redis failover"})
    incident_id = create_res.get_json()["id"]

    resolve_res = client.post(f"/api/incidents/{incident_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.get_json()["status"] == "RESOLVED"

def test_simulate_error(client):
    """Test that simulate-error responds with 500"""
    res = client.get("/api/simulate-error")
    assert res.status_code == 500
    assert res.get_json()["code"] == 500
