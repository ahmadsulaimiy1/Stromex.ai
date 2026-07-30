from enum import Enum as PyEnum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=PyEnum)


def pg_enum(enum_cls: type[E], name: str) -> SAEnum:
    """A Postgres ENUM column that stores each member's `.value` ("admin"),
    not its Python name ("ADMIN") — SQLAlchemy's default. Keeps the database
    representation identical to what the API serializes over JSON, so a raw
    `WHERE role = 'admin'` query behaves exactly as every caller expects."""
    return SAEnum(enum_cls, name=name, values_callable=lambda obj: [member.value for member in obj])
