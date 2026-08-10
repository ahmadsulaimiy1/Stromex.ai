"""Single import point for every mapped model.

Importing this module populates `Base.metadata` and, as a side effect of the
`TenantOwned.__init_subclass__` hook, `TENANT_OWNED_MODELS`. The RLS applier
and the generated isolation tests both read that registry, so a new model
gets a policy and a test by existing — not by anyone remembering.
"""

from app.db.base import TENANT_OWNED_MODELS, Base
from app.modules.audit.models import AuditEvent, SecurityEvent
from app.modules.authz.models import (
    MembershipRole,
    Role,
    RolePermission,
)
from app.modules.identity.models import (
    Membership,
    User,
    UserSession,
)
from app.modules.tenancy.models import Tenant, TenantDomain

__all__ = [
    "TENANT_OWNED_MODELS",
    "AuditEvent",
    "Base",
    "Membership",
    "MembershipRole",
    "Role",
    "RolePermission",
    "SecurityEvent",
    "Tenant",
    "TenantDomain",
    "User",
    "UserSession",
]
