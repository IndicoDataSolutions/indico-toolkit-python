class EtlOutputError(Exception):
    """
    Raised when an error occurs accessing `EtlOutput` values.
    """


class TokenNotFoundError(EtlOutputError):
    """
    Raised when a `Token` can't be found for a `Span`.
    """


class TableCellNotFoundError(EtlOutputError):
    """
    Raised when a `Table` and `Cell` can't be found for a `Token`.
    """
