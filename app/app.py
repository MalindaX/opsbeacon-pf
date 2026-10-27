import os
import time
import random
from flask import Flask, render_template, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import CollectorRegistry
from app.models import db, Incident

def create_app():
    app = Flask(__name__)

    # Database configuration (PostgreSQL by default with SQLite fallback for local test)
    db_url = os.getenv("DATABASE_URL", "sqlite:///opsbeacon.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Initialize Prometheus Metrics instrumentation
    # Each app owns its metrics so repeated factory calls cannot collide.
    metrics = PrometheusMetrics(app, registry=CollectorRegistry())
    metrics.info("opsbeacon_app_info", "OpsBeacon Application Info", version="1.0.0")

    # Custom Prometheus Metrics
    incident_counter = metrics.counter(
        "opsbeacon_incidents_created_total",
        "Total number of incidents created in OpsBeacon",
        labels={"severity": lambda: request.json.get("severity", "UNKNOWN") if request.is_json else "UNKNOWN"}
    )
    simulated_errors_counter = metrics.counter(
        "opsbeacon_simulated_errors_total",
        "Total number of simulated error triggers"
    )

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        incidents = Incident.query.order_by(Incident.created_at.desc()).limit(20).all()
        return render_template("index.html", incidents=incidents)

    @app.route("/health")
    def health():
        """Liveness & Readiness probe endpoint"""
        try:
            # Simple DB ping
            db.session.execute(db.text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        status_code = 200 if "unhealthy" not in db_status else 503
        return jsonify({
            "status": "healthy" if status_code == 200 else "degraded",
            "database": db_status,
            "version": "1.0.0"
        }), status_code

    @app.route("/api/incidents", methods=["GET"])
    def get_incidents():
        incidents = Incident.query.order_by(Incident.created_at.desc()).all()
        return jsonify([inc.to_dict() for inc in incidents]), 200

    @app.route("/api/incidents", methods=["POST"])
    @incident_counter
    def create_incident():
        data = request.get_json() or {}
        title = data.get("title")
        if not title:
            return jsonify({"error": "Title is required"}), 400

        incident = Incident(
            title=title,
            service_name=data.get("service_name", "core-api"),
            severity=data.get("severity", "MEDIUM"),
            status="OPEN"
        )
        db.session.add(incident)
        db.session.commit()
        return jsonify(incident.to_dict()), 201

    @app.route("/api/incidents/<int:incident_id>/resolve", methods=["POST"])
    def resolve_incident(incident_id):
        incident = Incident.query.get_or_404(incident_id)
        incident.status = "RESOLVED"
        db.session.commit()
        return jsonify(incident.to_dict()), 200

    @app.route("/api/simulate-load")
    def simulate_load():
        """Simulate variable server processing latency for metrics demonstration"""
        delay = random.uniform(0.05, 0.45)
        time.sleep(delay)
        return jsonify({"message": "Load simulation completed", "latency_seconds": round(delay, 3)}), 200

    @app.route("/api/simulate-error")
    @simulated_errors_counter
    def simulate_error():
        """Simulate a 500 internal server error for Grafana alerts testing"""
        return jsonify({"error": "Simulated 500 Internal Server Error", "code": 500}), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
