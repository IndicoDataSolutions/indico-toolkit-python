import itertools
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING

from ..results import Box, Span
from .errors import TableCellNotFoundError, TokenNotFoundError
from .table import Table
from .token import Token

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .cell import Cell


@dataclass(frozen=True)
class EtlOutput:
    text: str
    text_on_page: "tuple[str, ...]"

    tokens: "tuple[Token, ...]"
    tokens_on_page: "tuple[tuple[Token, ...], ...]"

    tables: "tuple[Table, ...]"
    tables_on_page: "tuple[tuple[Table, ...], ...]"

    @staticmethod
    def from_pages(
        text_pages: "Iterable[str]",
        token_dict_pages: "Iterable[Iterable[object]]",
        table_dict_pages: "Iterable[Iterable[object]]",
    ) -> "EtlOutput":
        """
        Create an `EtlOutput` from pages of text, tokens, and tables.
        """
        text_pages = tuple(text_pages)
        token_pages = tuple(
            tuple(sorted(map(Token.from_dict, token_dict_page), key=attrgetter("span")))
            for token_dict_page in token_dict_pages
        )
        table_pages = tuple(
            tuple(sorted(map(Table.from_dict, table_dict_page), key=attrgetter("box")))
            for table_dict_page in table_dict_pages
        )

        return EtlOutput(
            text="\n".join(text_pages),
            text_on_page=text_pages,
            tokens=tuple(itertools.chain.from_iterable(token_pages)),
            tokens_on_page=token_pages,
            tables=tuple(itertools.chain.from_iterable(table_pages)),
            tables_on_page=table_pages,
        )

    def token_for(self, span: Span) -> Token:
        """
        Return a `Token` that contains every character from `span`.
        Raise `TokenNotFoundError` if one can't be produced.
        """
        try:
            tokens = self.tokens_on_page[span.page]
            first = bisect_right(tokens, span.start, key=attrgetter("span.end"))
            last = bisect_left(tokens, span.end, lo=first, key=attrgetter("span.start"))
            tokens = tokens[first:last]
        except (IndexError, ValueError) as error:
            raise TokenNotFoundError(f"no token contains {span!r}") from error

        return Token(
            text=self.text[span.slice],
            box=Box(
                page=span.page,
                top=min(token.box.top for token in tokens),
                left=min(token.box.left for token in tokens),
                right=max(token.box.right for token in tokens),
                bottom=max(token.box.bottom for token in tokens),
            ),
            span=span,
        )

    def table_cell_for(self, token: Token) -> "tuple[Table, Cell]":
        """
        Return the `Table` and `Cell` that contain the midpoint of `token`.
        Raise `TableCellNotFoundError` if it's not inside a table cell.
        """
        token_vmid = (token.box.top + token.box.bottom) // 2
        token_hmid = (token.box.left + token.box.right) // 2

        for table in self.tables_on_page[token.box.page]:
            if (
                (table.box.top  <= token_vmid <= table.box.bottom) and
                (table.box.left <= token_hmid <= table.box.right)
            ):  # fmt: skip
                break
        else:
            raise TableCellNotFoundError(f"no table contains {token!r}")

        try:
            row_index = bisect_left(
                table.rows, token_vmid, key=lambda row: row[0].box.bottom
            )
            row = table.rows[row_index]

            cell_index = bisect_left(row, token_hmid, key=attrgetter("box.right"))
            cell = row[cell_index]
        except (IndexError, ValueError) as error:
            raise TableCellNotFoundError(f"no cell contains {token!r}") from error

        return table, cell
