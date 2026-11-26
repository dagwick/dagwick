# Airflow 3 with the latest Dagwick release from PyPI, for trying it out
# locally. Not a production image: see compose.yaml for what is switched off.
FROM apache/airflow:slim-3.3.2-python3.12@sha256:a54e7bd6c4d7a17e55cd14b0ead257877b8f8111680d2692cbdba2ff32bd3ff3

# Always the latest release: the version is kept only in src/dagwick/__init__.py.
# Dagwick has no dependencies of its own, so this never changes Airflow's.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade dagwick
