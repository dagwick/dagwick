"""Turn check results into linter diagnostics: one problem, one line, one place in the file.

``dagwick check`` prints them like Ruff does::

    dags/sales.py:15:2: DW103 dagrun_timeout is not set.

The checks run on the DAG as Airflow loaded it, which has no line numbers, so the
place comes from the DAG file's source, read with ``ast`` (never run):

- findings that name a line (``line 7: ...``) point at that line;
- findings about one task point at its ``task_id=`` or its ``@task`` function;
- DAG settings point at the argument when it is there (``catchup=True``), else at
  the ``DAG(...)`` call or ``@dag`` decorator; ``default_args`` settings point at
  their key, else at ``default_args``;
- findings about the whole file (its name, its parse time) point at line 1.
"""

from __future__ import annotations

import ast
import re
import tokenize
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from io import StringIO
from typing import Any

FAILED = ("fail", "warn")
LINE_ITEM = re.compile(r"^line (\d+)(?::\s*(.*))?$")
NOQA = re.compile(r"#\s*noqa(?::\s*(?P<codes>[\w\s,]+))?", re.IGNORECASE)

# How one item of a finding reads as a problem, per built-in check.
PROBLEM = {
    "retries": "Task doesn't retry",
    "execution_timeout": "Task has no execution_timeout",
    "failure_alerts": "Task doesn't alert on failure",
    "naming": "Not snake_case",
    "isolated_tasks": "Task isn't connected to any other task",
    "sensor_slots": "Sensor",
    "current_imports": "Deprecated import",
    "hardcoded_secrets": "Secret in the code",
    "parse_time_variables": "Variable.get runs on every parse",
    "dynamic_start_date": "start_date changes on every parse",
    "depends_on_past": "depends_on_past",
}
# DAG arguments a check is about: the diagnostic points at the argument when it is set.
DAG_ARGUMENT = {
    "dagrun_timeout": "dagrun_timeout",
    "catchup": "catchup",
    "max_active_runs": "max_active_runs",
    "auto_pause": "max_consecutive_failed_dag_runs",
    "schedule": "schedule",
    "tags": "tags",
    "docs": "doc_md",
    "deadline_alerts": "deadline",
}
# Settings that usually live in default_args: point at their key, else at default_args.
DEFAULT_ARG = {
    "owner": "owner",
    "retries": "retries",
    "execution_timeout": "execution_timeout",
    "failure_alerts": "on_failure_callback",
    "retry_alerts": "on_retry_callback",
}
WHOLE_FILE = {"file_name", "parse_time"}


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    line: int
    col: int
    code: str
    message: str
    check_id: str = ""
    dag_id: str = ""
    fix: str = ""  # "safe", "unsafe" or "" when dagwick fix can't fix it


Position = tuple[int, int]  # 1-based line and column


def _decorator_name(node: ast.expr) -> str:
    target = node.func if isinstance(node, ast.Call) else node
    while isinstance(target, ast.Attribute):
        if target.attr in ("dag", "task"):
            return target.attr
        target = target.value
    return target.id if isinstance(target, ast.Name) else ""


def _str_arg(call: ast.Call, name: str, position: int | None = None) -> str | None:
    for kw in call.keywords:
        value = kw.value
        if kw.arg == name and isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    if position is not None and len(call.args) > position:
        arg = call.args[position]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


class Locator:
    """Where things are in one DAG file: DAG definitions, tasks and default_args."""

    def __init__(self, source: str | None) -> None:
        self.lines = StringIO(source or "", newline="").readlines()
        try:
            self.tree: ast.Module | None = ast.parse(source) if source else None
        except (SyntaxError, ValueError):
            self.tree = None
        self.dags: dict[str, ast.AST] = {}  # dag_id -> DAG(...) call or @dag decorator
        self.dag_calls: dict[str, ast.Call | None] = {}  # dag_id -> the call with its args
        self.first_dag: ast.AST | None = None
        self.tasks: dict[str, ast.AST] = {}
        self.assigned: dict[str, ast.AST] = {}  # variable -> its value (for default_args)
        if self.tree:
            self._scan(self.tree)

    def _scan(self, tree: ast.Module) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assigned.setdefault(target.id, node.value)
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None
            ):
                self.assigned.setdefault(node.target.id, node.value)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    kind = _decorator_name(deco)
                    call = deco if isinstance(deco, ast.Call) else None
                    if kind == "dag":
                        dag_id = (call and _str_arg(call, "dag_id", 0)) or node.name
                        self._add_dag(dag_id, deco, call)
                    elif kind == "task":
                        task_id = (call and _str_arg(call, "task_id")) or node.name
                        self.tasks.setdefault(task_id, node)
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                )
                if name == "DAG":
                    dag_id = _str_arg(node, "dag_id", 0)
                    if dag_id:
                        self._add_dag(dag_id, node, node)
                    elif self.first_dag is None:
                        self.first_dag = node
                task_id = _str_arg(node, "task_id")
                if task_id:
                    self.tasks.setdefault(task_id, node)

    def _add_dag(self, dag_id: str, node: ast.AST, call: ast.Call | None) -> None:
        self.dags.setdefault(dag_id, node)
        self.dag_calls.setdefault(dag_id, call)
        if self.first_dag is None or node.lineno < self.first_dag.lineno:
            self.first_dag = node

    def pos(self, node: ast.AST) -> Position:
        line = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
        col = len(line.encode("utf-8")[: node.col_offset].decode("utf-8", errors="ignore"))
        return node.lineno, col + 1

    def line_start(self, lineno: int) -> Position:
        line = self.lines[lineno - 1] if 0 < lineno <= len(self.lines) else ""
        return lineno, len(line) - len(line.lstrip()) + 1

    def dag(self, dag_id: str) -> Position:
        node = self.dags.get(dag_id) or self.first_dag
        return self.pos(node) if node is not None else (1, 1)

    def _dag_keyword(self, dag_id: str, name: str) -> ast.keyword | None:
        call = self.dag_calls.get(dag_id)
        if call is None and dag_id not in self.dags and isinstance(self.first_dag, ast.Call):
            call = self.first_dag
        return next((kw for kw in call.keywords if kw.arg == name), None) if call else None

    def dag_argument(self, dag_id: str, name: str) -> Position:
        kw = self._dag_keyword(dag_id, name)
        return self.pos(kw) if kw is not None else self.dag(dag_id)

    def default_arg(self, dag_id: str, key: str) -> Position:
        kw = self._dag_keyword(dag_id, "default_args")
        value: ast.AST | None = kw.value if kw is not None else None
        if isinstance(value, ast.Name):
            value = self.assigned.get(value.id, value)
        elif value is None:
            value = self.assigned.get("default_args")
        if isinstance(value, ast.Dict):
            for k in value.keys:
                if isinstance(k, ast.Constant) and k.value == key:
                    return self.pos(k)
            return self.pos(value)
        if kw is not None:
            return self.pos(kw)
        return self.dag(dag_id)

    def task(self, task_id: str, dag_id: str) -> Position:
        node = self.tasks.get(task_id)
        return self.pos(node) if node is not None else self.dag(dag_id)

    def noqa(self, lineno: int) -> tuple[bool, frozenset[str]] | None:
        """A ``# noqa`` comment on this line: (blanket, codes), or None."""
        if not 0 < lineno <= len(self.lines):
            return None
        try:
            tokens = list(tokenize.generate_tokens(StringIO(self.lines[lineno - 1]).readline))
        except (tokenize.TokenError, SyntaxError, IndentationError):
            tokens = []
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                m = NOQA.search(tok.string)
                if m:
                    codes = m.group("codes")
                    if not codes:
                        return True, frozenset()
                    listed = (c.strip().upper() for c in codes.split(","))
                    return False, frozenset(c for c in listed if c)
        return None


def _place(loc: Locator, check_id: str, dag_id: str) -> Position:
    if check_id in WHOLE_FILE:
        return 1, 1
    if check_id in DAG_ARGUMENT:
        return loc.dag_argument(dag_id, DAG_ARGUMENT[check_id])
    if check_id in DEFAULT_ARG:
        return loc.default_arg(dag_id, DEFAULT_ARG[check_id])
    return loc.dag(dag_id)


def diagnostics(report: dict[str, Any], loc: Locator, fixable: dict[str, str]) -> list[Diagnostic]:
    """The problems in one DAG's report, each with its place in the file."""
    path, dag_id = report.get("file", ""), report["dag_id"]
    found = []
    for c in report["checks"]:
        if c["status"] not in FAILED:
            continue
        check_id, code = c["id"], c.get("code") or c["id"]
        common = {"path": path, "code": code, "check_id": check_id, "dag_id": dag_id}
        common["fix"] = fixable.get(check_id, "")
        problem = PROBLEM.get(check_id, c["title"])
        if not c["items"] or check_id in WHOLE_FILE:
            line, col = _place(loc, check_id, dag_id)
            found.append(Diagnostic(line=line, col=col, message=c["message"], **common))
            continue
        for item in c["items"]:
            m = LINE_ITEM.match(item)
            if m:
                line, col = loc.line_start(int(m.group(1)))
                detail = m.group(2) or ""
                message = f"{problem}: {detail}" if detail else c["message"]
            elif check_id == "naming" and item == dag_id:
                line, col = loc.dag(dag_id)
                message = f"{problem}: dag_id `{item}`"
            elif check_id == "sensor_slots":
                task_id = item.split(":", 1)[0]
                line, col = loc.task(task_id, dag_id)
                message = f"{problem} `{task_id}`{item[len(task_id) :]}"
            else:
                line, col = loc.task(item, dag_id)
                message = f"{problem}: `{item}`"
            found.append(Diagnostic(line=line, col=col, message=message, **common))
    return found


def _matches(d: Diagnostic, patterns: Iterable[str]) -> bool:
    return any(d.code.upper().startswith(p.upper()) or d.check_id == p for p in patterns)


def selected(
    found: Iterable[Diagnostic],
    select: Sequence[str] = (),
    ignore: Sequence[str] = (),
    locators: dict[str, Locator] | None = None,
) -> list[Diagnostic]:
    """Keep the diagnostics ``select`` asks for, drop ``ignore`` and ``# noqa`` lines."""
    out = []
    for d in found:
        if select and not _matches(d, select):
            continue
        if ignore and _matches(d, ignore):
            continue
        loc = (locators or {}).get(d.path)
        noqa = loc.noqa(d.line) if loc else None
        if noqa and (noqa[0] or any(d.code.upper().startswith(c) for c in noqa[1])):
            continue
        out.append(d)
    return sorted(set(out))


def line(d: Diagnostic) -> str:
    mark = " [*]" if d.fix == "safe" else ""
    return f"{d.path}:{d.line}:{d.col}: {d.code}{mark} {d.message}"


def summary(found: Sequence[Diagnostic], grades: Sequence[str]) -> list[str]:
    """The lines after the diagnostics: how many, how many fixable, the grades."""
    out = []
    if found:
        files = len({d.path for d in found})
        noun = "error" if len(found) == 1 else "errors"
        out.append(f"Found {len(found)} {noun} in {files} file{'' if files == 1 else 's'}.")
        safe = sum(d.fix == "safe" for d in found)
        unsafe = sum(d.fix == "unsafe" for d in found)
        if safe:
            more = f" ({unsafe} more with `--unsafe-fixes`)" if unsafe else ""
            out.append(f"[*] {safe} fixable with `dagwick fix --write`{more}.")
        elif unsafe:
            out.append(f"{unsafe} fixable with `dagwick fix --write --unsafe-fixes`.")
    else:
        out.append("All checks passed!")
    if grades:
        counts = {g: grades.count(g) for g in "ABCDF" if g in grades}
        spread = ", ".join(f"{n} {g}" for g, n in counts.items())
        out.append(f"{len(grades)} DAG{'' if len(grades) == 1 else 's'} graded: {spread}.")
    return out
