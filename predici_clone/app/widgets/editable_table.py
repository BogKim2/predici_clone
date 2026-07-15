from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from predici_clone.app.widgets.species_icon import color_tokens


class EditableTableWidget(QTableWidget):
    """Common editable table behavior used across the professional GUI."""

    def __init__(self, rows: int = 0, columns: int = 0, parent=None) -> None:
        super().__init__(rows, columns, parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)

    def append_row(self, values: tuple[object, ...] | list[object]) -> int:
        row = self.rowCount()
        self.insertRow(row)
        for column, value in enumerate(values):
            self.setItem(row, column, QTableWidgetItem(str(value)))
        return row

    def remove_selected_rows(self) -> int:
        rows = sorted({index.row() for index in self.selectedIndexes()}, reverse=True)
        for row in rows:
            self.removeRow(row)
        return len(rows)

    def duplicate_selected_rows(self) -> int:
        rows = sorted({index.row() for index in self.selectedIndexes()})
        inserted = 0
        for row in rows:
            values = [
                self.item(row, column).text() if self.item(row, column) is not None else ""
                for column in range(self.columnCount())
            ]
            self.append_row(values)
            inserted += 1
        return inserted

    def move_selected_row(self, offset: int) -> bool:
        row = self.currentRow()
        target = row + int(offset)
        if row < 0 or target < 0 or target >= self.rowCount():
            return False
        values = [
            self.item(row, column).text() if self.item(row, column) is not None else ""
            for column in range(self.columnCount())
        ]
        self.removeRow(row)
        self.insertRow(target)
        for column, value in enumerate(values):
            self.setItem(target, column, QTableWidgetItem(value))
        self.selectRow(target)
        return True

    def mark_invalid_rows(self, rows: set[int] | list[int] | tuple[int, ...]) -> None:
        color = QColor(color_tokens()["color.error"])
        for row in rows:
            for column in range(self.columnCount()):
                item = self.item(int(row), column)
                if item is not None:
                    item.setForeground(color)
