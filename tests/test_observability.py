from __future__ import annotations

import pytest
from conftest import roundtrip

from dagwick.core import score_dag


def _notify(context):  # pragma: no cover - never called
    pass


def _checks(**default_args):
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.sdk import DAG

    with DAG("alerts", schedule=None, default_args=default_args) as dag:
        EmptyOperator(task_id="a")
        EmptyOperator(task_id="b")
    return {c["id"]: c for c in score_dag(roundtrip(dag))["checks"]}


@pytest.mark.parametrize(
    ("default_args", "status", "kind"),
    [
        ({"email": "team@example.com", "email_on_failure": True}, "pass", "by an email"),
        ({"on_failure_callback": _notify}, "pass", "by a callback"),
        ({}, "fail", None),
        # Airflow turns email_on_failure on by default: without an address it sends nothing.
        ({"email_on_failure": True}, "fail", None),
        ({"email": "team@example.com", "email_on_failure": False}, "fail", None),
    ],
)
def test_failure_alerts(default_args, status, kind):
    check = _checks(**default_args)["failure_alerts"]
    assert check["status"] == status
    if kind:
        assert kind in check["message"]


@pytest.mark.parametrize(
    ("default_args", "status", "kind"),
    [
        ({"email": "team@example.com", "email_on_retry": True}, "pass", "by an email"),
        ({"on_retry_callback": _notify}, "pass", "by a callback"),
        ({}, "warn", None),
        ({"email_on_retry": True}, "warn", None),
        ({"email": "team@example.com", "email_on_retry": False}, "warn", None),
    ],
)
def test_retry_alerts(default_args, status, kind):
    check = _checks(**default_args)["retry_alerts"]
    assert check["status"] == status
    if kind:
        assert kind in check["message"]


def test_failure_alerts_mixes_callbacks_and_emails():
    from airflow.providers.standard.operators.empty import EmptyOperator
    from airflow.sdk import DAG

    with DAG("mixed", schedule=None) as dag:
        EmptyOperator(task_id="a", on_failure_callback=_notify)
        EmptyOperator(task_id="b", email="team@example.com", email_on_failure=True)
        EmptyOperator(task_id="c")
    check = {c["id"]: c for c in score_dag(roundtrip(dag))["checks"]}["failure_alerts"]
    assert check["status"] == "warn"
    assert check["items"] == ["c"]
