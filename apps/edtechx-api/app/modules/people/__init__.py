"""People, relationships, and enrolment history.

Both model modules are imported here so that importing either one gives
SQLAlchemy a complete picture — `enrolments` points at `student_relationships`,
and importing the smaller half first left that foreign key unresolvable in
whichever test happened to do it.
"""

from app.modules.people import enrolment, models  # noqa: F401
