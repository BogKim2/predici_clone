"""Script compatibility helpers."""

from predici_clone.script.commands import ScriptCommandState, script_command_namespace
from predici_clone.script.function_catalog import ScriptFunctionSpec, script_function_catalog
from predici_clone.script.template import generate_script_template

__all__ = [
    "ScriptCommandState",
    "ScriptFunctionSpec",
    "generate_script_template",
    "script_command_namespace",
    "script_function_catalog",
]
