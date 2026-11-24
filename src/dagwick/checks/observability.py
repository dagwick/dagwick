from __future__ import annotations

from typing import Any

from dagwick.checks._util import coverage
from dagwick.core import Category, Finding, Status, check


def _emails(task: Any, flag: str) -> bool:
    """True if Airflow will email someone: the flag is on and an address is set.

    Airflow turns ``email_on_failure`` and ``email_on_retry`` on by default, so
    the flag alone means nothing without an ``email``.
    """
    return bool(getattr(task, flag, False)) and bool(getattr(task, "email", None))


def _kinds(callback: bool, email: bool) -> str:
    if callback and email:
        return "a callback or an email"
    return "a callback" if callback else "an email"


def _failure_callback(task: Any) -> bool:
    return bool(getattr(task, "has_on_failure_callback", False))


@check(
    id="failure_alerts",
    title="Someone hears about failures",
    category=Category.OBSERVABILITY,
    weight=15,
    ack_hint="where failures are alerted instead (e.g. a central listener or a Grafana rule)",
    example=(
        'default_args={"on_failure_callback": send_slack_alert}  '
        '# or {"email": "team@example.com", "email_on_failure": True}'
    ),
    fix=(
        "Add on_failure_callback (e.g. a Slack notifier) in default_args, "
        "or set email with email_on_failure=True."
    ),
)
def failure_alerts(dag: Any) -> Finding:
    if getattr(dag, "has_on_failure_callback", False):
        return Finding(Status.PASS, "The DAG has an on_failure_callback.")
    tasks = list(dag.tasks)
    by_callback = any(_failure_callback(t) for t in tasks)
    by_email = any(_emails(t, "email_on_failure") and not _failure_callback(t) for t in tasks)
    return coverage(
        dag,
        lambda t: _failure_callback(t) or _emails(t, "email_on_failure"),
        noun="alert on failure",
        all_msg=f"Every task alerts on failure by {_kinds(by_callback, by_email)}.",
        none_msg="Nothing alerts on failure; it will fail silently.",
    )


@check(
    id="retry_alerts",
    title="Retries are visible",
    category=Category.OBSERVABILITY,
    weight=3,
    acknowledgeable=True,
    example=(
        'default_args={"on_retry_callback": send_slack_alert}  '
        '# or {"email": "team@example.com", "email_on_retry": True}'
    ),
    fix=(
        "Add on_retry_callback, or set email with email_on_retry=True, so flaky "
        "tasks surface before they start failing."
    ),
)
def retry_alerts(dag: Any) -> Finding:
    tasks = list(dag.tasks)
    by_callback = any(getattr(t, "has_on_retry_callback", False) for t in tasks)
    by_email = any(_emails(t, "email_on_retry") for t in tasks)
    if by_callback or by_email:
        return Finding(
            Status.PASS, f"Retries send a notification by {_kinds(by_callback, by_email)}."
        )
    return Finding(Status.WARN, "Retries happen silently.")
