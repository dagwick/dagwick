# Dagwick demo

A throwaway Airflow 3 with the latest Dagwick release from PyPI and the demo
DAGs from [`dev/dags`](../dev/dags). Needs Docker.

From the repository root:

```bash
docker compose -f demo/compose.yaml up
```

Open <http://localhost:8080> and click **Dagwick** in the sidebar. Each DAG
also has a **Dagwick** tab. The first start takes a minute or two while the
image builds.

Grade the same DAGs from the command line:

```bash
docker compose -f demo/compose.yaml run --rm airflow bash -c "dagwick check /opt/airflow/dags"
```

Stop it with `Ctrl+C`, and remove it with:

```bash
docker compose -f demo/compose.yaml down --rmi local
```

**Sandbox only.** There is no login, so anyone who can reach it is an admin.
It listens on `127.0.0.1` only, and nothing is kept once the container is
removed. Never use these settings for a real deployment; see the main
[README](../README.md#setup) to install Dagwick in your own Airflow.

To work on Dagwick itself, with a live UI build, use `dev/run.sh` instead.
