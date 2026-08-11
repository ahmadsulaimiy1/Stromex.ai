"""Structural guarantees that keep the architecture from eroding quietly.

Module boundaries and route coverage are the two things that degrade first in a
growing codebase, and they degrade invisibly. Asserting them mechanically is
cheaper than noticing later.
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from fastapi.routing import APIRoute

from app.main import app

APP_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULES_ROOT = APP_ROOT / "modules"


# --- module boundaries ----------------------------------------------------

# A module owns its tables. Another module reads them through the owning
# module's service layer, never by importing its models
# (EDTECHX_ARCHITECTURE.md §3).
# Empty, and intended to stay that way. Cross-module relationships are
# declared by string name so SQLAlchemy can resolve them at mapper
# configuration without the owning module importing the other's models.
MODEL_IMPORT_EXCEPTIONS: dict[str, set[str]] = {}


def _module_of(path: pathlib.Path) -> str:
    return path.relative_to(MODULES_ROOT).parts[0]


def _imports(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
        elif isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
    return found


def _module_files() -> list[pathlib.Path]:
    return [p for p in MODULES_ROOT.rglob("*.py") if p.name != "__init__.py"]


def test_modules_exist() -> None:
    assert _module_files(), "No module files found — has the layout changed?"


@pytest.mark.parametrize("path", _module_files(), ids=lambda p: str(p.name))
def test_no_module_imports_another_modules_models(path: pathlib.Path) -> None:
    owner = _module_of(path)
    allowed = MODEL_IMPORT_EXCEPTIONS.get(owner, set())
    for imported in _imports(path):
        if not imported.startswith("app.modules."):
            continue
        parts = imported.split(".")
        if len(parts) < 4:
            continue
        other, submodule = parts[2], parts[3]
        if other == owner or other in allowed:
            continue
        assert submodule != "models", (
            f"{path.relative_to(APP_ROOT)} imports {imported}. A module owns its "
            f"tables; read {other}'s data through its service layer instead."
        )


def test_core_does_not_depend_on_modules() -> None:
    """`core` is the foundation. If it knows about a module, the layering is inverted."""
    for path in (APP_ROOT / "core").glob("*.py"):
        offending = [i for i in _imports(path) if i.startswith("app.modules.")]
        assert not offending, f"app/core/{path.name} imports {offending}"


def test_ai_provider_sdks_are_confined_to_their_adapters() -> None:
    """No `import anthropic` outside its adapter (EDTECHX_AI_ARCHITECTURE.md §1).

    Enforced from the start so the gateway abstraction cannot rot the moment
    somebody needs "just one quick call".
    """
    sdk_names = {"anthropic", "openai", "google", "deepseek"}
    for path in APP_ROOT.rglob("*.py"):
        if "tests" in path.parts or "providers" in path.parts:
            continue
        for imported in _imports(path):
            root = imported.split(".")[0]
            assert root not in sdk_names, (
                f"{path.relative_to(APP_ROOT)} imports {imported} directly. "
                "Provider SDKs belong in app/modules/intelligence/providers/."
            )


# --- route coverage -------------------------------------------------------

# Routes that intentionally require no *permission*. Two different things are
# listed here and the distinction matters: some are reachable with no principal
# at all (health, context, sign-in, refresh), and some require authentication
# but grant nothing beyond the caller's own identity (/me, sign-out). Adding to
# this set is a security decision and is reviewed as one.
ROUTES_WITHOUT_PERMISSION: set[tuple[str, str]] = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/context"),
    # /me is authenticated but grants nothing beyond the caller's own identity.
    ("GET", "/api/v1/me"),
    # Authenticated, and returns only what this person may already see: the
    # navigation is itself computed from their permissions, so a permission
    # guarding it would be checking the same thing twice.
    ("GET", "/api/v1/experience"),
    # Authentication must be reachable before a principal exists. These are the
    # most exposed routes in the product and are guarded by rate limiting and
    # uniform responses rather than by permission.
    ("POST", "/api/v1/auth/sign-in"),
    ("POST", "/api/v1/auth/refresh"),
    # Authenticated, but signs out only the caller's own session.
    ("POST", "/api/v1/auth/sign-out"),
    # Completes a sign-in that already passed the password step; the challenge
    # token is the authority, and no principal exists yet.
    ("POST", "/api/v1/auth/mfa/verify"),
    # Authenticated, and act only on the caller's own second factor. Removal
    # additionally requires elevation.
    ("POST", "/api/v1/auth/mfa/enrol"),
    ("POST", "/api/v1/auth/mfa/activate"),
    ("DELETE", "/api/v1/auth/mfa"),
}

DOC_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def _api_routes() -> list[object]:
    """Flatten the application's routes across FastAPI's routing shapes.

    Recent FastAPI versions wrap `include_router` results in an internal
    `_IncludedRouter` rather than splicing `APIRoute` objects into
    `app.routes`. Both shapes expose `path`, `methods`, and `dependant`, which
    is all this check needs — so we accept either rather than pinning a
    version and silently checking nothing when it changes.
    """
    collected: list[object] = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            collected.append(route)
            continue
        contexts = getattr(route, "effective_route_contexts", None)
        if callable(contexts):
            collected.extend(contexts())
    return [
        r
        for r in collected
        if getattr(r, "path", "").startswith("/api/")
        and not getattr(r, "path", "").startswith(DOC_PREFIXES)
    ]


def _guards_a_permission(route: object) -> bool:
    from app.api.deps import RequirePermission

    dependant = getattr(route, "dependant", None)
    if dependant is not None:
        stack = [dependant]
        seen: set[int] = set()
        while stack:
            current = stack.pop()
            if id(current) in seen:
                continue
            seen.add(id(current))
            if isinstance(getattr(current, "call", None), RequirePermission):
                return True
            stack.extend(getattr(current, "dependencies", []) or [])
    return any(
        isinstance(getattr(d, "dependency", None), RequirePermission)
        for d in getattr(route, "dependencies", []) or []
    )


def test_there_are_routes_to_check() -> None:
    assert _api_routes()


@pytest.mark.parametrize(
    "route", _api_routes(), ids=lambda r: f"{sorted(r.methods)[0]} {r.path}"
)
def test_every_route_is_guarded_or_explicitly_public(route: APIRoute) -> None:
    method = sorted(route.methods)[0]
    if (method, route.path) in ROUTES_WITHOUT_PERMISSION:
        return
    assert _guards_a_permission(route), (
        f"{method} {route.path} declares no permission and is not listed in "
        "ROUTES_WITHOUT_PERMISSION. Every route must do one or the other."
    )


# --- scoped resources are read through the scoped helpers -----------------

# Tables whose rows belong to some people and not others. A `select()` over one
# of these outside the authorization layer is a query with no scope in it, and
# the fact that it is *currently* only reachable by an administrator is not a
# guarantee — the next handler added beside it inherits the pattern.
SCOPED_MODELS = {
    "StudentRelationship",
    "Enrolment",
    "EnrolmentEvent",
    "Person",
    "GuardianRelationship",
    "QualificationAward",
    # A candidature is one person's, and the record of who supervises whom is
    # among the most sensitive things a graduate school holds. Added when the
    # tables were, rather than the first time somebody wrote a handler over
    # them — which is the only moment at which adding it is free.
    "Supervision",
    "SupervisionMeeting",
    "Milestone",
}

# Where an unscoped `select()` over those models is legitimate, and why.
UNSCOPED_SELECT_ALLOWED = {
    # Owns the tables: the service layer is what the scoped helpers are built
    # on, and its callers are responsible for the scope.
    "app/modules/people/service.py",
    "app/modules/people/scopes.py",
    # Owns the research tables, on the same terms. Every *read* a person
    # performs here goes through `scoped_select`; what is left unscoped is the
    # administrative write path, whose caller holds the permission.
    "app/modules/academics/supervision.py",
    "app/modules/academics/scopes.py",
    # Builds the predicates themselves.
    "app/modules/authz/predicates.py",
}


# The four helpers that cannot produce a statement without an authorization
# predicate. Anything else taking a scoped model is suspect.
SANCTIONED_CALLS = {"scoped_select", "scoped_count", "scoped_get", "scoped_exists"}


def _selects_over(path: pathlib.Path) -> set[str]:
    """Every call in this file that takes a scoped model, minus the sanctioned ones.

    Inverted deliberately. An earlier version of this check listed the *unsafe*
    call names — `select`, `delete`, `update` — and a sabotage walked straight
    past it by writing `from sqlalchemy import select as _select`. A check that
    a rename defeats is a check that measures nothing, so this one treats every
    call as unsafe unless it is one of the four that carry a predicate by
    construction.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name in SANCTIONED_CALLS:
            continue
        # The model *class*, not one of its columns. `order_by(Person.name)`
        # narrows nothing and hides nothing; `db.get(Person, id)` is a fetch
        # with no predicate at all, and that is what this is looking for.
        first = node.args[0]
        if isinstance(first, ast.Name) and first.id in SCOPED_MODELS:
            found.add(f"{name}({first.id})")
    return found


def test_routes_do_not_query_scoped_tables_directly() -> None:
    """A handler that builds its own query is a handler with no scope in it.

    `scoped_select` is the sanctioned path precisely because it cannot be used
    without producing a predicate. A route that reaches for `select(Person)`
    instead has removed the boundary — not deliberately, usually, but by
    copying the line above it.
    """
    offenders: list[str] = []
    for path in (APP_ROOT / "api").rglob("*.py"):
        for call in sorted(_selects_over(path)):
            offenders.append(f"{path.relative_to(APP_ROOT)}: {call}")
    assert not offenders, (
        "A route queries a scoped table directly. Use "
        "`authz.predicates.scoped_select`, which cannot produce a statement "
        "without an authorization predicate:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize(
    "path",
    [p for p in MODULES_ROOT.rglob("*.py") if p.name != "__init__.py"],
    ids=lambda p: str(p.name),
)
def test_modules_do_not_query_scoped_tables_outside_their_owner(
    path: pathlib.Path,
) -> None:
    """The same rule inside the modules, with the owner and the compiler exempt.

    The exemptions are named individually and each has a reason. A module that
    needs to read people's records asks `people.service`, which is where the
    decision about what is scoped and what is not belongs.
    """
    relative = str(path.relative_to(APP_ROOT.parent).as_posix()).removeprefix("app/")
    if f"app/{relative}" in UNSCOPED_SELECT_ALLOWED:
        return
    found = _selects_over(path)
    assert not found, (
        f"{relative} queries {sorted(found)} directly. Read them through "
        "`people.service`, or — where the caller is authorization-sensitive — "
        "through `authz.predicates.scoped_select`."
    )
