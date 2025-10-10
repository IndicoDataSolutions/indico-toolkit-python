from dataclasses import dataclass
from operator import attrgetter

from .box import Box
from .cell import Cell
from .utils import get


@dataclass(frozen=True)
class Table:
    box: Box
    cells: "tuple[Cell, ...]"
    rows: "tuple[tuple[Cell, ...], ...]"
    columns: "tuple[tuple[Cell, ...], ...]"

    @staticmethod
    def from_dict(table: object) -> "Table":
        """
        Create a `Table` from a table dictionary.
        """
        page = get(table, int, "page_num")
        get(table, dict, "position")["page_num"] = page
        row_count = get(table, int, "num_rows")
        column_count = get(table, int, "num_columns")

        cells = tuple(
            sorted(
                (Cell.from_dict(cell, page) for cell in get(table, list, "cells")),
                key=attrgetter("range"),
            )
        )
        cells_by_row_col = {
            (row, column): cell
            for cell in cells
            for row in cell.range.rows
            for column in cell.range.columns
        }
        rows = tuple(
            tuple(
                cells_by_row_col[row, column]
                for column in range(column_count)
            )
            for row in range(row_count)
        )  # fmt: skip
        columns = tuple(
            tuple(
                cells_by_row_col[row, column]
                for row in range(row_count)
            )
            for column in range(column_count)
        )  # fmt: skip

        return Table(
            box=Box.from_dict(get(table, dict, "position")),
            cells=cells,
            rows=rows,
            columns=columns,
        )
