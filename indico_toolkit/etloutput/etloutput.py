import itertools
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING

from .box import Box
from .errors import TokenNotFoundError
from .span import Span
from .table import Table
from .token import Token

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

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
            assert tokens
        except (AssertionError, IndexError, ValueError) as error:
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

    def table_cells_for(self, span: Span) -> "Iterator[tuple[Table, Cell]]":
        """
        Yield the table cells that overlap with `span`.
        """
        if 0 <= span.page < len(self.tables_on_page):
            for table in self.tables_on_page[span.page]:
                if any(span & table_span for table_span in table.spans):
                    for cell in table.cells:
                        if any(span & cell_span for cell_span in cell.spans):
                            yield table, cell
