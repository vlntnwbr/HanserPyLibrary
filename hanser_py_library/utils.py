"""Exceptions and utility functions for hanser-py-library"""

from dataclasses import dataclass
from io import BytesIO
from typing import Optional


class BookMetaError(Exception):
    "Error that occurs while parsing website for the book"


class BookMergeError(Exception):
    """Error that occurs while merging the book"""


class DownloadError(Exception):
    """Exception that occurs while the book is downloaded"""


@dataclass
class Chapter:
    """Container for titel, url and content of a book chapter"""

    title: str
    href: Optional[str] = None
    content: Optional[BytesIO] = None


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
