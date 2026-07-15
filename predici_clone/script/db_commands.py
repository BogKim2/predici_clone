from __future__ import annotations

from predici_clone.db.parameter_db import ParameterDatabase


def db_command_namespace(database: ParameterDatabase) -> dict[str, object]:
    return {
        "dbpar": database.dbpar,
        "dbfunc": database.dbfunc,
    }
