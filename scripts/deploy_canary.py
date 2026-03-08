#!/usr/bin/env python3
"""
Canary Deployment Script.

Deploys model to canary, monitors health, and promotes or rolls back.
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from finetune.infrastructure.deployment.health_checker import HealthChecker
from finetune.infrastructure.registry.mlflow_registry import MLflowRegistry
from finetune.infrastructure.observability.notification_client import get_notification_client


def load_config(config_path: str) -> dict:
    """Load canary config."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def deploy_canary(
    version: str,
    traffic_percent: int = 10,
    config_path: str = "configs/deployment/canary.yml",
) -> bool:
    """Deploy model to canary.

    Args:
        version: Model version to deploy
        traffic_percent: Initial traffic percentage
        config_path: Path to canary config

    Returns:
        True if deployment successful
    """
    config = load_config(config_path)
    canary_config = config.get("canary", {})
    health_config = config.get("health_checks", {})
    mlflow_config = config.get("mlflow", {})

    print(f"🚀 Deploying canary for version {version} with {traffic_percent}% traffic")

    # Initialize MLflow registry
    mlflow_registry = MLflowRegistry(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        registered_model_name=mlflow_config.get("model_name", "emotion-classifier"),
    )

    # Transition model to Staging (canary)
    try:
        mlflow_registry.promote_to_staging(version)
        print(f"✅ Model {version} promoted to Staging")
    except Exception as e:
        print(f"❌ Failed to promote to Staging: {e}")
        return False

    # Initialize health checker
    health_checker = HealthChecker(
        health_endpoint=os.getenv("HEALTH_ENDPOINT", "http://localhost:8000/health"),
        metrics_endpoint=os.getenv("METRICS_ENDPOINT", "http://localhost:8000/metrics"),
        check_interval=health_config.get("check_interval", 30),
        timeout=health_config.get("timeout", 10),
    )

    # Wait for canary to become healthy
    print("⏳ Waiting for canary health check...")
    is_healthy = health_checker.wait_for_healthy(
        success_threshold=health_config.get("success_threshold", 3),
        failure_threshold=health_config.get("failure_threshold", 3),
        error_rate_threshold=health_config.get("metrics", {}).get("error_rate_threshold", 1.0),
        latency_p95_threshold=health_config.get("metrics", {}).get("latency_p95_threshold", 500),
        availability_threshold=health_config.get("metrics", {}).get("availability_threshold", 99.0),
    )

    if not is_healthy:
        print("❌ Canary health check failed - initiating rollback")
        rollback(version, config_path)
        return False

    print("✅ Canary is healthy!")

    # Auto-promote if configured
    if config.get("promotion", {}).get("auto_promote", True):
        print(f"🚀 Auto-promoting to {traffic_percent + 10}% traffic")

        # Gradual traffic increase
        traffic_increments = canary_config.get("traffic_increments", [25, 50, 75, 100])
        increment_interval = canary_config.get("increment_interval", 300)

        for next_traffic in traffic_increments:
            if next_traffic <= traffic_percent:
                continue

            print(f"📈 Increasing traffic to {next_traffic}%")

            # In practice, this would update the traffic split in your load balancer
            # For now, just wait and check health
            import time
            time.sleep(increment_interval)

            result = health_checker.check(
                error_rate_threshold=health_config.get("metrics", {}).get("error_rate_threshold", 1.0),
                latency_p95_threshold=health_config.get("metrics", {}).get("latency_p95_threshold", 500),
            )

            if result.status.value != "healthy":
                print(f"❌ Health check failed at {next_traffic}% traffic - rolling back")
                rollback(version, config_path)
                return False

        # All increments passed - promote to production
        print("🎉 All canary checks passed - promoting to production")
        promote_to_production(version, config_path)

    return True


def promote_to_production(
    version: str,
    config_path: str = "configs/deployment/canary.yml",
) -> bool:
    """Promote canary to production.

    Args:
        version: Model version
        config_path: Path to canary config

    Returns:
        True if promotion successful
    """
    config = load_config(config_path)
    mlflow_config = config.get("mlflow", {})

    mlflow_registry = MLflowRegistry(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        registered_model_name=mlflow_config.get("model_name", "emotion-classifier"),
    )

    try:
        mlflow_registry.promote_to_production(version)
        print(f"✅ Model {version} promoted to Production")

        # Send notification
        notification = get_notification_client()
        notification.notify_promotion(
            version=version,
            decision="promote",
            reason="All canary checks passed",
        )
        return True
    except Exception as e:
        print(f"❌ Failed to promote to Production: {e}")
        return False


def rollback(
    version: str,
    config_path: str = "configs/deployment/canary.yml",
) -> bool:
    """Rollback to previous version.

    Args:
        version: Version to rollback from
        config_path: Path to canary config

    Returns:
        True if rollback successful
    """
    config = load_config(config_path)
    mlflow_config = config.get("mlflow", {})

    print(f"🔄 Rolling back from version {version}")

    mlflow_registry = MLflowRegistry(
        tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        registered_model_name=mlflow_config.get("model_name", "emotion-classifier"),
    )

    # Find previous production version
    # In practice, you'd query MLflow for the previous version
    previous_version = os.getenv("PREVIOUS_VERSION")

    if previous_version:
        try:
            mlflow_registry.promote_to_production(previous_version)
            print(f"✅ Rolled back to previous version {previous_version}")

            # Send notification
            notification = get_notification_client()
            notification.notify_promotion(
                version=version,
                decision="rollback",
                reason=f"Rolled back to {previous_version}",
            )
            return True
        except Exception as e:
            print(f"❌ Failed to rollback: {e}")
            return False
    else:
        print("⚠️ No previous version found for rollback")
        return False


def main():
    parser = argparse.ArgumentParser(description="Canary deployment")
    parser.add_argument("--version", required=True, help="Model version to deploy")
    parser.add_argument("--traffic", type=int, default=10, help="Initial traffic percent")
    parser.add_argument("--config", default="configs/deployment/canary.yml", help="Config path")
    parser.add_argument("--promote", action="store_true", help="Skip canary, promote directly")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version")

    args = parser.parse_args()

    if args.rollback:
        success = rollback(args.version, args.config)
    elif args.promote:
        success = promote_to_production(args.version, args.config)
    else:
        success = deploy_canary(args.version, args.traffic, args.config)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
