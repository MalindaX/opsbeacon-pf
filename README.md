# OpsBeacon

OpsBeacon is a small incident management web app with a monitoring and CI/CD setup. It lets users create and resolve incidents, and exposes application metrics for monitoring.

## Screenshots

**Grafana dashboard**

![OpsBeacon Grafana dashboard](assets/Grafana%20Dashboard.png)

**Prometheus data source in Grafana**

![Prometheus data source configuration](assets/prom%20data%20source.png)

**CI/CD pipelines**

| GitHub Actions | Jenkins |
| --- | --- |
| ![GitHub Actions workflow](assets/github%20actions.png) | ![Successful Jenkins build](assets/Jenkins%20Build%20Success.png) |

## Built with

- Python 3.11 and Flask
- PostgreSQL, SQLAlchemy, and SQLite for tests
- Docker and Docker Compose
- Prometheus and Grafana
- Jenkins and GitHub Actions
- Pytest and Flake8

## Features

- Create, view, and resolve incidents
- Health check endpoint at `/health`
- Prometheus metrics at `/metrics`
- Endpoints to simulate load and errors for monitoring
- Automated tests, Docker image builds, and image publishing in CI/CD pipelines

## Run locally

1. Install Docker and Docker Compose.
2. Start the app and database:

   ```bash
   docker compose up --build
   ```

3. Open [http://localhost:5000](http://localhost:5000).

## Monitoring

Start Prometheus and Grafana from the `monitoring` directory:

```bash
docker compose -f docker-compose.monitoring.yml up -d
```

- Grafana: [http://localhost:3000](http://localhost:3000)
- Prometheus: [http://localhost:9090](http://localhost:9090)

## CI/CD

- GitHub Actions runs lint checks and tests on pushes and pull requests to `main`.
- On pushes to `main`, it builds and publishes the Docker image to Docker Hub.
- The Jenkins pipeline also tests and builds the image, publishes it, and supports optional local deployment.
