"""The plans EdirasX sells, as a definition rather than as logic.

Rows, seeded from here. `EDTECHX_BILLING.md` §1: no price, plan name or limit
appears in application logic, and a grep for a plan name outside this module is
a defect.

Every key is prefixed `plan.` so that a plan key reads as one everywhere it
appears — and so the check in `test_entitlements.py` can be exact rather than
approximate. Without the prefix, the plan named "institution" collided with the
`institution.*` permission module, and a check that cries wolf gets deleted
rather than obeyed.

**Free is genuinely useful.** Every core school operation is on it — attendance,
assessment, report cards, announcements, bulk import — because a school that
cannot take a register is not using the product, and a crippled free tier
teaches a school that the product is poor rather than that the paid tier is
good. What Free caps is scale, AI, and customization depth.
"""

from __future__ import annotations

PLANS: dict[str, dict] = {
    "plan.free": {
        "name": "Free",
        "tier": 0,
        "description": "Everything a small school needs to run, with capped scale.",
        "features": (
            "core.attendance",
            "core.assessment",
            "core.report_cards",
            "core.announcements",
            "core.bulk_import",
            "customization.terminology",
            "learning.courses",
        ),
        "limits": {
            "students.active": 150,
            "staff.active": 20,
            "storage.megabytes": 2000,
            "campuses": 1,
            "custom_roles": 0,
            "ai.tokens": 0,
            "documents.rendered": 200,
            "messages.sent": 500,
        },
    },
    "plan.standard": {
        "name": "Standard",
        "tier": 10,
        "description": "The whole school operating system, with room to grow.",
        "features": (
            "core.attendance", "core.assessment", "core.report_cards",
            "core.announcements", "core.bulk_import",
            "finance.invoicing", "finance.online_payments",
            "customization.theme", "customization.terminology",
            "learning.courses", "learning.quizzes",
            "intelligence.assistants",
            "operations.timetabling",
        ),
        "limits": {
            "students.active": 1500,
            "staff.active": 200,
            "storage.megabytes": 50_000,
            "campuses": 3,
            "custom_roles": 10,
            "ai.tokens": 2_000_000,
            "ai.requests": 20_000,
            "documents.rendered": 20_000,
            "messages.sent": 50_000,
            "exports.generated": 2_000,
        },
    },
    "plan.institution": {
        "name": "Institution",
        "tier": 20,
        "description": "Multi-campus, white-label, and the studios.",
        "features": (
            "core.attendance", "core.assessment", "core.report_cards",
            "core.announcements", "core.bulk_import",
            "finance.invoicing", "finance.online_payments",
            "customization.theme", "customization.terminology",
            "customization.custom_domain", "customization.white_label",
            "customization.design_studio", "customization.ai_design_studio",
            "learning.courses", "learning.quizzes",
            "intelligence.assistants", "intelligence.own_api_keys",
            "operations.sso", "operations.advanced_analytics",
            "operations.api_access", "operations.timetabling",
        ),
        "limits": {
            # `None` is unlimited, and is not the same answer as a large number.
            "students.active": None,
            "staff.active": None,
            "storage.megabytes": None,
            "campuses": None,
            "custom_roles": None,
            "ai.tokens": 20_000_000,
            "ai.requests": 250_000,
            "documents.rendered": None,
            "messages.sent": None,
            "exports.generated": None,
        },
    },
}
