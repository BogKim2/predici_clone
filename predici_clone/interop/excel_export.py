from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


def export_workbook(path: str | Path, sheets: dict[str, list[dict[str, object]]]) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, rows in sheets.items():
        sheet = workbook.create_sheet(title=name[:31])
        headers = list(rows[0]) if rows else []
        if headers:
            sheet.append(headers)
            for row in rows:
                sheet.append([row.get(header) for header in headers])
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(destination)
    return destination
