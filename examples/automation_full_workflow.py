from __future__ import annotations

from pathlib import Path

from predici_clone.api import run_automation_workflow


def main() -> None:
    output = Path("automation_run.npz")
    payload = run_automation_workflow(export_path=output)
    print(f"recipe={payload['project'].recipe.name}")
    print(f"points={payload['points'].shape[0]}")
    print(f"Mw={payload['moments']['Mw']:.6g}")
    print(f"npz={output}")


if __name__ == "__main__":
    main()
