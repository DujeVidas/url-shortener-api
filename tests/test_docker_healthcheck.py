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

def test_api_prevents_privilege_escalation():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert "no-new-privileges:true" in api["security_opt"]


def test_api_drops_linux_capabilities():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert api["cap_drop"] == ["ALL"]


def test_api_has_read_only_root_filesystem():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert api["read_only"] is True


def test_api_has_writable_temporary_filesystem():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert "/tmp:rw,nosuid,nodev,size=64m" in api["tmpfs"]

def test_all_services_use_json_file_logging():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    services = config["services"]

    for service_name in ("api", "db", "redis"):
        logging_config = services[service_name]["logging"]

        assert logging_config["driver"] == "json-file"


def test_all_services_have_log_rotation():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    services = config["services"]

    for service_name in ("api", "db", "redis"):
        options = services[service_name]["logging"]["options"]

        assert options["max-size"] == "10m"
        assert options["max-file"] == "3"

def test_api_has_graceful_shutdown_period():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert api["stop_grace_period"] == "30s"

def test_api_configures_database_connect_timeout():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    api = config["services"]["api"]

    assert api["environment"]["DB_CONNECT_TIMEOUT"] == "5"

def test_api_configures_database_pool():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    environment = config["services"]["api"]["environment"]

    assert environment["DB_POOL_SIZE"] == "5"
    assert environment["DB_MAX_OVERFLOW"] == "5"
    assert environment["DB_POOL_TIMEOUT"] == "10"

def test_api_configures_database_pool_recycling():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    environment = config["services"]["api"]["environment"]

    assert environment["DB_POOL_RECYCLE"] == "1800"

def test_api_configures_database_statement_timeout():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    environment = config["services"]["api"]["environment"]

    assert environment["DB_STATEMENT_TIMEOUT_MS"] == "10000"

def test_api_configures_idle_transaction_timeout():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    environment = config["services"]["api"]["environment"]

    assert environment["DB_IDLE_TRANSACTION_TIMEOUT_MS"] == "60000"

def test_api_configures_request_body_limit():
    compose_file = PROJECT_ROOT / "compose.yaml"

    with compose_file.open() as file:
        config = yaml.safe_load(file)

    environment = config["services"]["api"]["environment"]

    assert environment["MAX_REQUEST_BODY_BYTES"] == "16384"