from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_api_has_docker_healthcheck():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert "healthcheck" in api

    healthcheck = api["healthcheck"]

    assert healthcheck["interval"] == "10s"
    assert healthcheck["timeout"] == "3s"
    assert healthcheck["retries"] == 3
    assert healthcheck["start_period"] == "30s"


def test_api_healthcheck_uses_liveness_endpoint():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    healthcheck = config["services"]["api"]["healthcheck"]

    command = " ".join(healthcheck["test"])

    assert "/health/live" in command
    assert "/health/ready" not in command

def test_all_services_have_restart_policy():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    services = config["services"]

    for service_name in ("api", "db", "redis"):
        assert services[service_name]["restart"] == "unless-stopped"

def test_all_services_have_memory_limits():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    services = config["services"]

    expected_limits = {
        "api": "512m",
        "db": "512m",
        "redis": "256m",
    }

    for service_name, expected_limit in expected_limits.items():
        assert services[service_name]["mem_limit"] == expected_limit