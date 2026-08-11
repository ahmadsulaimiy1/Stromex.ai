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
    TeachingAllocation,
)
from app.modules.academics.research import (
    Milestone,
    Supervision,
    SupervisionMeeting,
)
from app.modules.academics.structure import (
    AcademicUnit,
    Cohort,
    CreditSystem,
    MilestoneDefinition,
    Programme,
    Qualification,
    SupervisionRole,
)
from app.modules.assessment.models import (
    ApprovalRecord,
    ApprovalWorkflow,
    Assessment,
    AssessmentScore,
    PublishedResult,
    ResultAmendment,
    ResultSet,
)
from app.modules.attendance.models import (
    AttendanceAmendment,
    AttendanceCode,
    AttendanceMark,
    AttendanceSession,
)
from app.modules.audit.models import AuditEvent, SecurityEvent
from app.modules.authz.models import (
    MembershipRole,
    Role,
    RolePermission,
)
from app.modules.billing.models import (
    FeatureSetting,
    Plan,
    PlanFeature,
    PlanLimit,
    Subscription,
    SubscriptionOverride,
    UsageRecord,
)
from app.modules.customization.models import BrandingProfile, TerminologySet
from app.modules.documents.models import (
    Document,
    DocumentSequence,
    DocumentTemplate,
)
from app.modules.experience.models import InterfaceProfile, UserPreference
from app.modules.identity.models import (
    Membership,
    User,
    UserSession,
)
from app.modules.imports.models import ImportBatch, ImportRow
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
    "AcademicUnit",
    "AcademicYear",
    "ApprovalRecord",
    "ApprovalWorkflow",
    "Assessment",
    "AssessmentScore",
    "AttendanceAmendment",
    "AttendanceCode",
    "AttendanceMark",
    "AttendanceSession",
    "AuditEvent",
    "Base",
    "BrandingProfile",
    "ClassGroup",
    "Cohort",
    "CreditSystem",
    "Document",
    "DocumentSequence",
    "DocumentTemplate",
    "Enrolment",
    "EnrolmentEvent",
    "FeatureSetting",
    "GradingBand",
    "GradingScale",
    "GuardianRelationship",
    "ImportBatch",
    "ImportRow",
    "InterfaceProfile",
    "Level",
    "Membership",
    "MembershipRole",
    "Milestone",
    "MilestoneDefinition",
    "Person",
    "Plan",
    "PlanFeature",
    "PlanLimit",
    "Programme",
    "ProgressionRule",
    "PublishedResult",
    "Qualification",
    "QualificationAward",
    "ResultAmendment",
    "ResultSet",
    "Role",
    "RolePermission",
    "SecurityEvent",
    "StaffRelationship",
    "StudentRelationship",
    "Subscription",
    "SubscriptionOverride",
    "Supervision",
    "SupervisionMeeting",
    "SupervisionRole",
    "TeachingAllocation",
    "Tenant",
    "TenantDomain",
    "TerminologySet",
    "UsageRecord",
    "User",
    "UserPreference",
    "UserSession",
]

# Runs once, after every model is mapped, because it needs the complete picture:
# whether a foreign key crosses the tenant boundary cannot be known until both
# ends exist.
TENANT_SCOPED_FOREIGN_KEYS = bind_foreign_keys_to_tenant(Base.metadata)
