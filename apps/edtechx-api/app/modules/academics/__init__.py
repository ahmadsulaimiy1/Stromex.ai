"""The academic engine.

Both model modules are imported here so that importing either one gives
SQLAlchemy a complete picture. `levels.programme_id` points at a table defined
in `structure`, and importing `models` alone left that foreign key unresolvable
— a failure that appeared far from its cause, in whichever test happened to
import the smaller half first.
"""

from app.modules.academics import models, structure  # noqa: F401
