# EdirasX Permission Model

**Version:** 1.0

---

## 1. Shape

Authorization answers one question:

> May **this membership**, holding **these roles** with **these scopes**, perform **this action** on **this resource**, inside **this tenant**, under **this plan**?

Six inputs, evaluated in a fixed order. Five of them are RBAC and one is ABAC; both are needed. Pure RBAC cannot express "a teacher may grade *their own* class"; pure ABAC becomes unauditable at institutional scale.

```
Principal = user + membership + roles + scopes + tenant
Decision  = tenant match ∧ entitlement ∧ permission ∧ scope ∧ resource state
```

---

## 2. Permission strings

`module.resource.action`, lowercase, dot-separated.

```
people.student.read        academics.class.write
attendance.mark.write      assessment.result.publish
finance.invoice.issue      customization.theme.publish
intelligence.design.approve  platform.tenant.suspend
```

Actions: `read · write · create · delete · approve · publish · export · manage`.
`manage` implies all actions on that resource and is used for administrative roles.

**Rules**
- Permissions are additive; there are no negative permissions. Denial is the absence of a grant. Negative permissions make effective-permission reasoning intractable and produce bugs nobody can explain to an auditor.
- Wildcards only at the trailing segment: `finance.invoice.*`, `finance.*`. Never `*.invoice.read`.
- The full permission catalogue is declared in one place and validated at startup; a role referencing an unknown permission fails the boot, not the request.

---

## 3. Scopes (the ABAC layer)

A role grant carries a scope narrowing *which* resources it applies to.

| Scope | Meaning |
|---|---|
| `tenant` | All resources in the school |
| `campus:{ids}` | Limited to campuses |
| `department:{ids}` | Limited to departments |
| `level:{ids}` | Limited to year groups |
| `class:{ids}` | Limited to specific classes |
| `subject:{ids}` | Limited to subjects |
| `taught_by_self` | Resources attached to classes/subjects this membership teaches |
| `own_children` | Students linked to this membership as guardian |
| `self` | Records about this membership's own person |

Scopes are stored on `membership_roles.scope` as validated JSONB. A membership may hold the same role with different scopes (head of two departments), and scopes **union**.

Every scope compiles to a SQL predicate. This is deliberate: authorization must be expressible as a filter, not only as a yes/no on an already-loaded row, otherwise list endpoints leak by row count, and pagination becomes an oracle.

```python
Permission("attendance.mark.write") + Scope("taught_by_self")
→ EXISTS (SELECT 1 FROM class_subjects cs
          WHERE cs.class_group_id = attendance_sessions.class_group_id
            AND cs.teacher_membership_id = :membership_id)
```

---

## 4. System roles

Templates, not fixed law. Every one is clonable and editable by a school; a school may create roles we never imagined (Head of Boarding, Examinations Officer, Bursar's Assistant). System roles cannot be deleted while assigned, and their *keys* are stable so the platform can reason about them.

| Role | Default scope | Character |
|---|---|---|
| `owner` | tenant | Full control including billing, deletion, and role management |
| `admin` | tenant | Full operational control; cannot change billing or delete the tenant |
| `registrar` | tenant | People, enrolment, academics, records |
| `principal` | tenant | Read-wide, approve, publish; limited write |
| `head_of_department` | department | Manage subjects, staff, and results within the department |
| `teacher` | taught_by_self | Attendance, grading, assignments, communication for own classes |
| `form_tutor` | class | Teacher plus pastoral read across the tutor group |
| `bursar` | tenant | Finance module |
| `admissions_officer` | tenant | Admissions pipeline |
| `student` | self | Own courses, assignments, grades, timetable |
| `guardian` | own_children | Children's records, fees, communication |
| `support_staff` | configurable | Narrow, school-defined |
| `platform_operator` | cross-tenant metadata | Platform console; **no tenant content without break-glass** |

### 4.1 Tertiary and research roles

The templates above are school-shaped because most institutions are. They are
**templates, not the role set.** A university clones and renames them, or
creates its own: Chancellor, Vice-Chancellor, Rector, Provost, Registrar,
Deputy Registrar, Dean, Head of Department, Programme Coordinator, Lecturer,
Professor, Research Supervisor, Examiner, External Examiner, Academic Adviser,
Postgraduate Student, Research Student, Alumni.

None of these is hard-coded, and none needs to be: a role is a row with a name,
a permission set, and a scope. The scope kinds already cover the tertiary cases
— `department` reaches an academic unit and its descendants, and supervision is
expressed as a scope over the students a membership supervises.

The only platform-stable keys are the system templates' own, which exist so the
platform can reason about "the teacher role" without assuming what a given
institution put in it.

---

## 5. Evaluation order

Ordered so that the cheapest and most decisive checks run first, and so that error responses do not leak existence.

```
1  Authenticated?              → 401
2  Membership active in tenant?→ 403
3  Token tenant == host tenant?→ 403 + security event
4  Feature entitled by plan?   → 402 (with upgrade path)
5  Permission granted?         → 403
6  Scope predicate satisfied?  → 404   ← not 403
7  Resource state permits?     → 409
8  Rate limit / quota?         → 429
```

**Step 6 returns 404 on purpose.** If a teacher may not see class 9B, telling them "forbidden" confirms 9B exists. Absence of authority is presented as absence of resource. Step 5 may return 403 because the *capability* is not secret; step 6 concerns a specific resource, whose existence is.

---

## 6. Enforcement points

Authorization is enforced **in the service layer**, on the server, always.

- Routers declare required permissions declaratively; the dependency resolves the principal and asserts the permission before the handler runs.
- Services apply scope predicates to every query. There is no "load then check" path for list endpoints.
- The UI hides what a user cannot do — as a courtesy, never as a control. Every hidden control has a server-side equivalent that returns 403/404.
- A test enumerates every route and fails if one has neither an explicit permission requirement nor an explicit `@public` marker.

---

## 7. Sensitive-data overlays

Some fields are guarded beyond their table's permission.

| Field class | Rule |
|---|---|
| Medical / SEN notes | Separate permission `people.student.read_sensitive`; every read audited |
| Safeguarding records | Named individuals only; never visible through general student read; access always audited and notified |
| Custody / court orders | Restricted to designated roles; changes require dual approval |
| Financial detail on a family | Guardians with `receives_billing` only |
| Staff HR records | `institution.staff.read_hr`; never inherited from `admin` |

Redaction is applied at serialization time from the principal's permission set, so a field cannot escape through an endpoint that forgot to exclude it.

---

## 8. Delegation and elevation

- **Delegation:** an owner or admin may grant a role, but only permissions they themselves hold. Privilege cannot be manufactured by delegation.
- **Time-boxed grants:** `membership_roles.expires_at` supports cover arrangements (a teacher covering a colleague for two weeks) that expire without anyone remembering to revoke them.
- **Elevation:** actions marked high-risk (publishing results, voiding an invoice, deleting a student, changing another user's role) require a recent re-authentication — password or MFA within the last 10 minutes.
- **Dual control:** configurable per tenant for a defined set of actions (result publication, large refunds, tenant deletion). Two distinct memberships must approve.

---

## 9. Auditing

Every authorization *denial* at steps 5–7 is logged with principal, permission, resource, and reason. Denials are a signal in both directions: they surface misconfigured roles, and a spike of them from one principal is an attack indicator.

Every grant, revocation, scope change, and role edit is audited with before/after.

---

## 10. Testing

- **Matrix test:** every system role × every route class → expected allow/deny. Generated, not hand-written, so a new route without a matrix entry fails.
- **Scope tests:** a teacher can grade their own class and cannot grade another's; a guardian sees only their own children; a head of department sees only their department.
- **Escalation tests:** a user cannot grant a permission they lack; cannot edit their own roles; cannot widen their own scope; cannot reach another tenant by any parameter, header, or body field.
- **Redaction tests:** sensitive fields absent from every serializer for principals lacking the overlay permission.
- **The 404 test:** out-of-scope resources return 404, and response timing does not distinguish "missing" from "forbidden".
