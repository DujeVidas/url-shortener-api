from pathlib import Path


def test_startup_script_runs_migrations_before_server():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "scripts" / "start.sh"

    script = script_path.read_text()

    migration_command = "alembic upgrade head"
    server_command = "exec python -m app.run"

    assert migration_command in script
    assert server_command in script

    assert script.index(migration_command) < script.index(server_command)


def test_startup_script_stops_on_errors():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "scripts" / "start.sh"

    script = script_path.read_text()

    assert "set -eu" in script