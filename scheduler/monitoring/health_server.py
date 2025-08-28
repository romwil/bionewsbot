"""Health check and metrics server for BioNewsBot Scheduler."""
from flask import Flask, Response, jsonify
from prometheus_client import generate_latest
import structlog
from typing import Dict, Any
import psutil
import os
from datetime import datetime
from monitoring.metrics import metrics
from config.config import config


logger = structlog.get_logger(__name__)

app = Flask(__name__)


@app.route("/health")
def health_check() -> Response:
    """Health check endpoint."""
    try:
        health_status = metrics.get_health_status()
        
        # Add system resource information
        process = psutil.Process(os.getpid())
        health_status["resources"] = {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        }
        
        # Add Redis connectivity check
        try:
            import redis
            r = redis.Redis.from_url(config.redis.url)
            r.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "connected": True
            }
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Add API connectivity check
        try:
            import requests
            response = requests.get(
                f"{config.api.base_url}/health",
                timeout=5
            )
            health_status["checks"]["api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            health_status["checks"]["api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@app.route("/metrics")
def prometheus_metrics() -> Response:
    """Prometheus metrics endpoint."""
    try:
        # Update heartbeat
        metrics.heartbeat()
        
        # Update system metrics
        process = psutil.Process(os.getpid())
        metrics.update_worker_resources(
            worker_id="main",
            memory_mb=process.memory_info().rss / 1024 / 1024,
            cpu_percent=process.cpu_percent(interval=0.1)
        )
        
        # Generate metrics
        return Response(
            metrics.get_metrics(),
            mimetype="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error("metrics_error", error=str(e))
        return Response("Error generating metrics", status=500)


@app.route("/ready")
def readiness_check() -> Response:
    """Readiness check endpoint."""
    try:
        # Check if scheduler is ready to accept jobs
        checks = {
            "redis": False,
            "api": False,
            "workers": False
        }
        
        # Check Redis
        try:
            import redis
            r = redis.Redis.from_url(config.redis.url)
            r.ping()
            checks["redis"] = True
        except:
            pass
        
        # Check API
        try:
            import requests
            response = requests.get(f"{config.api.base_url}/health", timeout=5)
            checks["api"] = response.status_code == 200
        except:
            pass
        
        # Check workers
        checks["workers"] = metrics.active_workers._value.get() > 0
        
        ready = all(checks.values())
        
        return jsonify({
            "ready": ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }), 200 if ready else 503
        
    except Exception as e:
        logger.error("readiness_check_error", error=str(e))
        return jsonify({
            "ready": False,
            "error": str(e)
        }), 500


@app.route("/live")
def liveness_check() -> Response:
    """Liveness check endpoint."""
    # Simple check that the process is alive
    return jsonify({
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/stats")
def statistics() -> Response:
    """Get scheduler statistics."""
    try:
        # This would aggregate statistics from metrics
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "workers": {
                "active": int(metrics.active_workers._value.get())
            },
            "queues": {},
            "tasks": {},
            "system": {
                "uptime_seconds": (datetime.utcnow() - datetime.fromtimestamp(
                    psutil.Process(os.getpid()).create_time()
                )).total_seconds()
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error("statistics_error", error=str(e))
        return jsonify({"error": str(e)}), 500


def run_health_server(host: str = "0.0.0.0", port: int = None):
    """Run the health check server."""
    port = port or config.monitoring.prometheus_port
    logger.info("starting_health_server", host=host, port=port)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_health_server()
