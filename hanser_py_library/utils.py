"""Global values and utility functions for hanser-py-library"""

import textwrap

HANSER_URL = "https://www.hanser-elibrary.com"


def is_isbn(isbn: str, isbn10_allowed: bool = True) -> bool:
    """True if isbn returns valid ISBN-13 or ISBN-10 checksum"""

    if len(isbn) == 13 and isbn.isnumeric():
        checksum = (
            10 - sum(
                [int(n) * (3 ** (i % 2)) for i, n in enumerate(isbn)]
                ) % 10
            ) % 10

    elif len(isbn) == 10 and isbn[:-1].isnumeric() and isbn10_allowed:
        isbn_parts = list(isbn)
        if not isbn_parts[-1].isnumeric():
            if isbn_parts[-1] not in ("x", "X"):
                return False
            isbn_parts[-1] = "10"

        checksum = sum([int(n) * i for i, n in enumerate(isbn_parts, 1)]) % 11

    else:
        return False

    return bool(checksum == 0)


def log(cat: str, msg: str, div: int = None, div_char: str = "-") -> None:
    """Log categorized message with optional divider"""

    if "\n" in msg:
        msg = msg.replace("\n", "\n\t")

    line_length, indent = 79, 10
    log_msg = "{:" + str(indent) + "}{}"
    message = textwrap.fill(
        log_msg.format(cat.upper(), msg),
        width=line_length,
        tabsize=indent,
        replace_whitespace=False,
        subsequent_indent=" " * 10,
    )

    if div in (0, -1):
        print(div_char * line_length)
    print(message)
    if div in (0, 1):
        print(div_char * line_length)
