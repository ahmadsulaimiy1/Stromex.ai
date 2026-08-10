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
    # Authentication must be reachable before a principal exists. These are the
    # most exposed routes in the product and are guarded by rate limiting and
    # uniform responses rather than by permission.
    ("POST", "/api/v1/auth/sign-in"),
    ("POST", "/api/v1/auth/refresh"),
    # Authenticated, but signs out only the caller's own session.
    ("POST", "/api/v1/auth/sign-out"),
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
