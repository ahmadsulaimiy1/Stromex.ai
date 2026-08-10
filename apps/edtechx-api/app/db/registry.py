"""Single import point for every mapped model.

Importing this module populates `Base.metadata` and, as a side effect of the
`TenantOwned.__init_subclass__` hook, `TENANT_OWNED_MODELS`. The RLS applier
and the generated isolation tests both read that registry, so a new model
gets a policy and a test by existing — not by anyone remembering.

The last statement in this module is the third mechanism of the same kind:
every foreign key between two tenant-owned tables is rewritten to reference
`(tenant_id, id)`, because a foreign-key check is the one operation row-level
security does not govern. See `app.db.tenant_fk`.
"""

from app.db.base import TENANT_OWNED_MODELS, Base
from app.db.tenant_fk import bind_foreign_keys_to_tenant
from app.modules.academics.models import (
    AcademicStage,
    AcademicYear,
    ClassGroup,
    GradingBand,
    GradingScale,
    Level,
    ProgressionRule,
)
from app.modules.audit.models import AuditEvent, SecurityEvent
from app.modules.authz.models import (
    MembershipRole,
    Role,
    RolePermission,
)
from app.modules.customization.models import TerminologySet
from app.modules.identity.models import (
    Membership,
    User,
    UserSession,
)
from app.modules.people.enrolment import (
    Enrolment,
    EnrolmentEvent,
    QualificationAward,
)
from app.modules.people.models import (
    GuardianRelationship,
    Person,
    StaffRelationship,
    StudentRelationship,
)
from app.modules.tenancy.models import Tenant, TenantDomain

__all__ = [
    "TENANT_OWNED_MODELS",
    "AcademicStage",
    "AcademicYear",
    "AuditEvent",
    "Base",
    "ClassGroup",
    "Enrolment",
    "EnrolmentEvent",
    "GradingBand",
    "GradingScale",
    "GuardianRelationship",
    "Level",
    "Membership",
    "MembershipRole",
    "Person",
    "ProgressionRule",
    "QualificationAward",
    "Role",
    "RolePermission",
    "SecurityEvent",
    "StaffRelationship",
    "StudentRelationship",
    "Tenant",
    "TenantDomain",
    "TerminologySet",
    "User",
    "UserSession",
]

# Runs once, after every model is mapped, because it needs the complete picture:
# whether a foreign key crosses the tenant boundary cannot be known until both
# ends exist.
TENANT_SCOPED_FOREIGN_KEYS = bind_foreign_keys_to_tenant(Base.metadata)
